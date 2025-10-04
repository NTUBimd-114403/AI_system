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
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].help_text = ''
        self.fields['password2'].help_text = ''
        
        # 自訂錯誤訊息
        self.fields['password1'].error_messages = {
            'required': '請輸入密碼'
        }
        self.fields['password2'].error_messages = {
            'required': '請再次輸入密碼'
        }

    class Meta:
        model = User
        fields = ['email', 'nickname', 'password1', 'password2']

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("此電子郵件已被使用。")
        return email
    
    def clean_password2(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("兩次輸入的密碼不一致")
        return password2
