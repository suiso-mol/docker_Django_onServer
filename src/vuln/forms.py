import io
import pandas as pd
from datetime import datetime, date
from dateutil.relativedelta import relativedelta
from django.utils.text import slugify
from django.utils.translation import gettext as _
from django import forms
from django.core.validators import FileExtensionValidator
from django.core.exceptions import ValidationError
from .models import Server, Package, Content

'''
class DateSelectorWidget(forms.MultiWidget):
    def __init__(self, attrs=None):
        today = datetime.today()
        start_year = today + relativedelta(years=-7)
        next_year = today + relativedelta(years=1)
        days = [(day, day) for day in range(1, 32)]
        months = [(month, month) for month in range(1, 13)]
        years = [(year, year) for year in range(start_year.year, next_year.year)]
        widgets = [
            forms.Select(attrs={'class': 'form-control', 'style': 'width: 80px'}, choices=years),
            forms.Select(attrs={'class': 'form-control', 'style': 'width: 80px'}, choices=months),
            forms.Select(attrs={'class': 'form-control', 'style': 'width: 80px'}, choices=days),
        ]
        super().__init__(widgets, attrs)

    def decompress(self, value):
        if isinstance(value, date):
            return [value.day, value.month, value.year]
        elif isinstance(value, str):
            year, month, day = value.split('-')
            return [year, month, day]
        return [None, None, None]

    def value_from_datadict(self, data, files, name):
        year, month, day = super().value_from_datadict(data, files, name)
        # DateField expects a single string that it can parse into a date.
        return '{}-{}-{}'.format(year, month, day)
'''

class CSVUploadForm(forms.Form):
    file = forms.FileField(
        label='CSVファイル',
        help_text='※拡張子csvのファイルをアップロードしてください。',
        validators=[FileExtensionValidator(allowed_extensions=['csv'])]
    )

    def clean_file(self):
        file = self.cleaned_data['file']
        chk_csv = io.TextIOWrapper(file, encoding="cp932")
        try:
            df = pd.read_csv(chk_csv, encoding="Shift-JIS")
        except Exception as e:
            raise forms.ValidationError('csv読み込み時にエラーが発生しました('+str(e)+")。")
        # データ件数チェック
        if len(df) == 0:
            raise forms.ValidationError('投入データが存在しません。')
        # 更新対象サーバ件数チェック
        df_chk = df.drop_duplicates(subset="サーバ名")
        if len(df_chk) != 1:
            raise forms.ValidationError('投入データに複数のサーバが含まれています('+str(len(df_chk))+')。')
        
        self._instance = df.fillna("")
        return self
    
    def save(self):
        df = self._instance
        # Modelごとに更新用データを作成
        df_server = df.iloc[:,[0,1,2,3,4,10]].drop_duplicates(subset="サーバ名")
        df_package = df.iloc[:,[5,7,8,9,10]].drop_duplicates(subset="パッケージ名")
        df_content = df.iloc[:,[0,5,6,10]].drop_duplicates(subset=("サーバ名", "パッケージ名"))
#        print(1/0) # debug

        ## Server insert | update
        try:
            dbdata = Server.objects.get(name=df_server.iat[0,0])
            if df_server.iat[0,1]:
                dbdata.ip = df_server.iat[0,1]
            if df_server.iat[0,2]:
                dbdata.os = df_server.iat[0,2]
            if df_server.iat[0,3]:
                dbdata.usage = df_server.iat[0,3]
            if df_server.iat[0,4]:
                dbdata.remark = df_server.iat[0,4]
            if df_server.iat[0,5] == "DS":
                dbdata.deleted = True
            elif df_server.iat[0,5] == "RS":
                dbdata.deleted = False
            dbdata.save()
        except:
            Server.objects.create(name=df_server.iat[0,0], ip=df_server.iat[0,1], os=df_server.iat[0,2], usage=df_server.iat[0,3], remark=df_server.iat[0,4])
        ### 自動作成されるUUIDを取得
        sv_uuid = Server.objects.get(name=df_server.iat[0,0]).sv_id

        ## Package insert & update
        list_add = []
        list_del = []
        list_upd1 = []
        list_upd2 = []
        list_upd3 = []
        list_upd4 = []
        for d in df_package.itertuples():
            if d[1]:
                list_add.append(Package(pkg_name=d[1], architecture=d[2], description=d[3], remark=d[4]))
                if d[5] == "DP":
                    list_del.append(Package(pkg_name=d[1], deleted=True))
                elif d[5] == "RP":
                    list_del.append(Package(pkg_name=d[1], deleted=False))
                else:
                    if not d[3]:
                        if not d[4]:
                            list_upd1.append(Package(pkg_name=d[1], architecture=d[2]))
                        else:
                            list_upd2.append(Package(pkg_name=d[1], architecture=d[2], remark=d[4]))
                    else:
                        if not d[4]:
                            list_upd3.append(Package(pkg_name=d[1], architecture=d[2], description=d[3]))
                        else:
                            list_upd4.append(Package(pkg_name=d[1], architecture=d[2], description=d[3], remark=d[4]))

#        print(1/0) # debug

        ### 一括作成、既存のものは処理しない
        if len(list_add) > 0:
            Package.objects.bulk_create(list_add,ignore_conflicts=True)
        ### 一括更新
        if len(list_del) > 0:
            Package.objects.bulk_update(list_del, ['architecture', 'deleted'])
        if len(list_upd1) > 0:
            Package.objects.bulk_update(list_upd1, ['architecture'])
        if len(list_upd2) > 0:
            Package.objects.bulk_update(list_upd2, ['architecture', 'remark'])
        if len(list_upd3) > 0:
            Package.objects.bulk_update(list_upd3, ['architecture', 'description'])
        if len(list_upd4) > 0:
            Package.objects.bulk_update(list_upd4, ['architecture', 'description', 'remark'])

        ## Content insert & update
        list_upd = []
        list_del = []
        ### サーバ名をUUIDに置換
        df_content = df_content.replace({'サーバ名': {df_server.iat[0,0]: sv_uuid}})
        for d in df_content.itertuples():
            list_upd.append(Content(sv_pkg=slugify(df_server.iat[0,0]+'-'+d[2]), sv_id_id=d[1], pkg_name_id=d[2],version=d[3]))
            if d[4] == "DS" or d[4] == "DP":
                list_del.append(Content(sv_pkg=slugify(df_server.iat[0,0]+'-'+d[2]), deleted=True))
            elif d[4] == "RS" or d[4] == "RP":
                list_del.append(Content(sv_pkg=slugify(df_server.iat[0,0]+'-'+d[2]), deleted=False))
#        print(1/0) # debug
        if len(list_upd) > 0:
            ### 一括作成、既存のものは処理しない
            Content.objects.bulk_create(list_upd,ignore_conflicts=True)
            ### 一括更新
            Content.objects.bulk_update(list_upd, ['version'])
        if len(list_del) > 0:
            Content.objects.bulk_update(list_del, ['deleted'])

class SearchForm(forms.Form):
    target = forms.fields.ChoiceField(
        choices = (
            ('1', 'MyJVN'),
            ('2', 'NVD')
        ),
        initial=['1'],
        label='target',
        required=True,
        widget=forms.widgets.RadioSelect
    )

    cvss = forms.fields.ChoiceField(
        choices = (('1', '-'), ('2', '2'), ('3', '3')),
        label='cvss',
        widget=forms.Select(attrs={'class': 'form-control', 'style': 'width: 40px'})
    )

    severity = forms.fields.ChoiceField(
        choices = (('1', 'All'), ('2', 'LOW'), ('3', 'MEDIUM'), ('4', 'HIGH'),('5', 'CRITICAL')),
        label='severity',
        widget=forms.Select(attrs={'class': 'form-control', 'style': 'width: 100px'})
    )

    keyword = forms.CharField(required=False)

    today = datetime.today()
    last_week = today + relativedelta(days=-7)
    start_year = today + relativedelta(years=-7)
    next_year = today + relativedelta(years=1)
    days = [(day, str(day).zfill(2)) for day in range(1, 32)]
    months = [(month, str(month).zfill(2)) for month in range(1, 13)]
    years = [(year, year) for year in range(start_year.year, next_year.year)]

    start_year = forms.fields.ChoiceField(
        choices=years, initial=[last_week.year], label='start_year', required=True,
        widget=forms.Select(attrs={'class': 'form-control', 'style': 'width: 70px'})
        )
    start_month = forms.fields.ChoiceField(
        choices=months, initial=[last_week.month], label='start_month', required=True,
        widget=forms.Select(attrs={'class': 'form-control', 'style': 'width: 50px'})
        )
    start_day = forms.fields.ChoiceField(
        choices=days, initial=[last_week.day], label='start_day', required=True,
        widget=forms.Select(attrs={'class': 'form-control', 'style': 'width: 50px'})
        )
    end_year = forms.fields.ChoiceField(
        choices=years, initial=[today.year], label='end_year', required=True,
        widget=forms.Select(attrs={'class': 'form-control', 'style': 'width: 70px'})
        )
    end_month = forms.fields.ChoiceField(
        choices=months, initial=[today.month], label='end_month', required=True,
        widget=forms.Select(attrs={'class': 'form-control', 'style': 'width: 50px'})
        )
    end_day = forms.fields.ChoiceField(
        choices=days, initial=[today.day], label='end_day', required=True,
        widget=forms.Select(attrs={'class': 'form-control', 'style': 'width: 50px'})
        )

    cpe1 = forms.fields.ChoiceField(
        choices=(("-", "-"), ("h", "h"), ("o", "o"), ("a", "a")),
        label='cpe1',
        widget=forms.Select(attrs={'class': 'form-control', 'style': 'width: 40px'})
        )
    cpe2 = forms.CharField(required=False)
    cpe3 = forms.CharField(required=False)
    cpe4 = forms.CharField(required=False)
    cpe5 = forms.CharField(required=False)
    cpe6 = forms.CharField(required=False)
    cpe7 = forms.CharField(required=False)

    def clean(self):
        # date
        syear = self.cleaned_data['start_year']
        smonth = self.cleaned_data['start_month']
        sday = self.cleaned_data['start_day']
        eyear = self.cleaned_data['end_year']
        emonth = self.cleaned_data['end_month']
        eday = self.cleaned_data['end_day']
        sdate = str(syear)+str(smonth).zfill(2)+str(sday).zfill(2)
        edate = str(eyear)+str(emonth).zfill(2)+str(eday).zfill(2)
        if (int(sdate)-int(edate)) > 0:
            raise forms.ValidationError(_('Date period entered incorrectly.'), code="incorrectly-date")
        # keyword, cpe
        key = self.cleaned_data['keyword']
        target = self.cleaned_data['target']
        cpe2 = self.cleaned_data['cpe2']
        cpe3 = self.cleaned_data['cpe3']
        cpe4 = self.cleaned_data['cpe4']
        if target == "1":
            if not key:
                if all([cpe2, cpe3]):
                    pass
                else:
                    if any([cpe2, cpe3]):
                        raise forms.ValidationError(_('Vender, product are required for cpe search.'), code="incorrectly-cpe")
                    else:
                        raise forms.ValidationError(_('Please enter search keywords or cpeName.'), code="no-key")
        else:
            if all([cpe2, cpe3, cpe4]):
                pass
            else:
                if any([cpe2, cpe3, cpe4]):
                    raise forms.ValidationError(_('Vender, product, version are required for cpe search.'), code="incorrectly-cpe")

class SearchDbForm(forms.Form):
    item = forms.CharField(
        initial='',
        label='item',
        required = False,
    )

'''
    start_date = forms.DateField(
        widget=DateSelectorWidget(),
    )
    end_date = forms.DateField(
        widget=DateSelectorWidget(),
    )
'''
