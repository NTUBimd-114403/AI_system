from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model

User = get_user_model()

class RegisterForm(UserCreationForm):
    nickname = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-container', 'placeholder': '使用者名稱'}),
        help_text=''  # 移除預設提示
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-container', 'placeholder': '電子郵件'})
    )
    password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-container', 'placeholder': '密碼'})
    )
    password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-container', 'placeholder': '確認密碼'})
    )

    class Meta:
        model = User
        fields = ['email', 'nickname', 'password1', 'password2']

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("此電子郵件已被使用。")
        return email
