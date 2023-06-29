from django.shortcuts import render
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse
from django.views import generic
from django.views.generic import TemplateView
from django.http import HttpResponseRedirect, HttpResponse
from django.template import loader
from django.conf import settings
from .forms import ChatForm, SummarizeForm, AccountForm
from .models import Chatlog
import openai

class IndexViewHistory(LoginRequiredMixin, generic.ListView):
    template_name = 'history.html'
    context_object_name = 'history_list'
    def get_queryset(self):
        return Chatlog.objects.order_by('-relation_id', 'log_id')

def Login(request):
    if request.method == 'POST':
        ID = request.POST.get('userid')
        Pass = request.POST.get('password')

        user = authenticate(username=ID, password=Pass)

        if user:
            if user.is_active:
                login(request,user)
                return HttpResponseRedirect(reverse('chat:top'))
            else:
                return HttpResponse("アカウントが有効ではありません")
        else:
            return HttpResponse("ログインIDまたはパスワードが間違っています")
    else:
        return render(request, 'login.html')

class Register(TemplateView):
    def __init__(self):
        self.params = {
        "AccountCreate":False,
        "account_form": AccountForm(),
        }
        
    def get(self,request):
        self.params["account_form"] = AccountForm()
        self.params["AccountCreate"] = False
        return render(request,"register.html",context=self.params)

    def post(self,request):
        self.params["account_form"] = AccountForm(data=request.POST)

        if self.params["account_form"].is_valid():
            User = self.params["account_form"].save()
            User.set_password(User.password)
            User.save()            
            return HttpResponseRedirect(reverse('chat:login'))
        else:
            print(self.params["account_form"].errors)

        return render(request,"register.html",context=self.params)

@login_required
def Logout(request):
    logout(request)
    return HttpResponseRedirect(reverse('chat:login'))

@login_required
def top(request):
    params = {"UserID":request.user,}
    return render(request, "top.html",context=params)

@login_required
def chat(request):
    
    sw_test = 0
    sw_debug = 0

    # initialize
    sentence = ""
    messages_reverse = []
    debug1 = ""

    if request.method == "POST":
        form = ChatForm(request.POST)
#        form.fields["target_type"].disabled = ""
        if form.is_valid():
            sentence = form.cleaned_data['sentence']
            target = request.session['target'] = form.cleaned_data['target_type']
#            form.fields["target_type"].disabled = "True"
            # API call
            if sw_test == 0:
                openai.api_key = settings.OPENAI_API_KEY
                if target == "1":
                    system_content = "どんな言語で聞かれても常に日本語で応答してください"
                elif target == "2":
                    system_content = "どんな言語で聞かれても常に英語で応答してください"
                elif target == "3":
                    system_content = "どんな言語で聞かれても常にエスペラント語で応答してください"
                else:
                    system_content = "常に日本語で応答してください"

                user_message = [{"role": "user", "content": sentence}]
                role_message = [{"role": "system", "content": system_content}]

                if "messages" in request.session:
                    api_messages = role_message + request.session["messages"] + user_message
                else:
                    api_messages = role_message + user_message

                response = openai.ChatCompletion.create(
#                    model="gpt-4",
                    model="gpt-3.5-turbo",
                    messages=api_messages,
                )
                
                chat_results = response["choices"][0]["message"]["content"]

                if sw_debug == 0:
                    pass
                else:
                    debug1 = api_messages

                # 結果をDBに保管
                if request.session['id'] == "0":
                    # セッション開始1回目
                    Chatlog.objects.create(user=request.user, input_text=sentence, output_text=chat_results)
                    last_chat = Chatlog.objects.filter(user=request.user).latest("create_date")
                    request.session['id'] = str(last_chat.log_id)
                    last_chat.relation_id = last_chat.log_id
                    last_chat.save()
                else:
                    Chatlog.objects.create(user=request.user, relation_id=request.session['id'], input_text=sentence, output_text=chat_results)

                # messageをセッションに保管
                assistant_message = [{"role": "assistant", "content": chat_results}]
                if "messages" in request.session:
                    request.session["messages"] = request.session["messages"] + user_message + assistant_message
                else:
                    request.session["messages"] = user_message + assistant_message


            else:
                # テスト用
                wk_int = int(request.session['id'])
                wk_int += 1
                request.session['id'] = str(wk_int)
                request.session["messages"] = request.session["messages"] + [{"role": "user", "content": sentence}]
                request.session["messages"] = request.session["messages"] + [{"role": "assistant", "content": "results"}]
#                chat_results = sentence + "+result+" + request.session['id']
#                chat_input_latest = "test_in_latest"
#                chat_results_latest = "test_out_latest"
        else:
            # pass
            wk_int = int(request.session['id'])
            wk_int += 100
            request.session['id'] = str(wk_int)
    else:
        form = ChatForm()
        request.session['id'] = "0"
        request.session["messages"] = []
    
    # 実行履歴を逆順にして返す
    messages_len = len(request.session["messages"])
    if messages_len != 0:
        if messages_len >= 4:
            for i in range(messages_len-2, -1, -2):
                messages_reverse = messages_reverse + [request.session["messages"][i]] + [request.session["messages"][i+1]]
        else:
            messages_reverse = messages_reverse + [request.session["messages"][0]] + [request.session["messages"][1]]
            
    template = loader.get_template('chat.html')
    context = {
        'form': form,
        'id' : request.session['id'],
        'messages' : messages_reverse,
        'api_messages' : debug1
#        'chat_input' : sentence,
#        'chat_results': chat_results,
#        'chat_input_latest' : chat_input_latest,
#        'chat_results_latest': chat_results_latest
    }

    return HttpResponse(template.render(context, request))

@login_required
def summarize(request):
    
    sw_test = 0

    # initialize
    sentence = ""
    chat_results = ""

    if request.method == "POST":
        form = SummarizeForm(request.POST)
        if form.is_valid():
            sentence = form.cleaned_data['sentence']
            target = request.session['target'] = form.cleaned_data['target_type']
            # API call
            if sw_test == 0:
                openai.api_key = settings.OPENAI_API_KEY
                system_content = "あなたは優秀な新聞記者です。"
                if target == 1:
                    user_content = "短く要約してください。"
                elif target == 2:
                    user_content = "凄く短く要約してください。"
                elif target == 3:
                    user_content = "子供向けに短く要約してください。"
                else:
                    user_content = "一言で要約してください。"
                role_message = [{"role": "system", "content": system_content}]
                assistant_message = [{"role": "assistant", "content": sentence}]
                user_message = [{"role": "user", "content": user_content}]

                response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=role_message + assistant_message + user_message,
                )
                
                chat_results = response["choices"][0]["message"]["content"]

                # 結果をDBに保管
                Chatlog.objects.create(user=request.user, input_text=sentence, output_text=chat_results)
                last_chat = Chatlog.objects.filter(user=request.user).latest("create_date")
                request.session['id'] = str(last_chat.log_id)
                last_chat.relation_id = last_chat.log_id
                last_chat.save()
    else:
        form = SummarizeForm()
        request.session['id'] = "0"
        request.session["messages"] = []
    
    template = loader.get_template('summarize.html')
    context = {
        'form': form,
        'id' : request.session['id'],
        'input' : sentence,
        'output' : chat_results
    }

    return HttpResponse(template.render(context, request))
