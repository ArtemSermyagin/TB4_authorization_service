import os

from django.contrib.auth import login, authenticate
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import IntegrityError
from django.http import HttpResponseBadRequest
from django.shortcuts import redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import CreateView, TemplateView

from users.forms import AuthenticationForm
from users.models import User, Code, Referrals
from users.tasks import send_verify_code_for_number
from users.validators import generate_unique_invite_code


class HomePageView(TemplateView):
    template_name = 'users/index.html' # путь к шаблону


class UserLoginView(CreateView):
    form_class = AuthenticationForm #
    template_name = 'users/login.html' #
    success_url = reverse_lazy('users:login_verify') #

    def form_valid(self, form):
        if form.is_valid():
            user = User.objects.filter(phone=form.cleaned_data['phone']).first()
            if not user:
                user = form.save(commit=False)
                invite_code = generate_unique_invite_code(6)
                user.invite_code = invite_code
                user.is_active = False
                user.save()

            # Тут логика отправки кода из 4 символов
            send_verify_code_for_number.apply_async(
                (user.id,),
                countdown=os.getenv(
                    'COUNTDOWN_SEND_CODE',
                    default=5
                )
            )
            self.request.session['user_id'] = user.id
        return redirect(self.success_url)


class UserVerifyView(TemplateView):
    template_name = 'users/verify.html'

    def post(self, request, *args, **kwargs):
        user_id = self.request.session.get('user_id')
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return redirect('users:login')

        if not Code.objects.filter(
                user=user,
                code="".join(request.POST.getlist('code'))
        ):
            return redirect('users:login_verify')
        login(request, user, backend='users.backend.PhoneBackend')
        return redirect('users:home')


class UserInviteCodeView(LoginRequiredMixin, View):

    def post(self, request, *args, **kwargs):
        if Referrals.objects.filter(user=request.user):
            return HttpResponseBadRequest("Вы уже являетесь чьим-то рефералом!")

        invite_code = request.POST['invite_code']
        # Пользователь, инвайт код которого мы ввели
        author = get_object_or_404(User, invite_code=invite_code)
        if author == request.user:
            return HttpResponseBadRequest("Вы не можете подписаться на самого себя!")

        try:
            Referrals.objects.create(
                user=request.user,
                author=author
            )
        except IntegrityError:
            return HttpResponseBadRequest("Вы уже являетесь рефералом этого пользователя!")

        return redirect('users:home')
