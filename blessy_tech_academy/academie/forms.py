from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User

from .models import Inscription, Formation


class InscriptionForm(forms.ModelForm):
    """Formulaire d'inscription/contact lié au model Inscription."""

    class Meta:
        model = Inscription
        fields = [
            'prenom',
            'nom',
            'email',
            'telephone',
            'formation',
            'sujet',
            'message',
        ]
        widgets = {
            'prenom': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Jean Raymond',
            }),
            'nom': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'BELONY',
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'exemple@email.com',
            }),
            'telephone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+509 XXXX XXXX',
            }),
            'formation': forms.Select(attrs={
                'class': 'form-control',
            }),
            'sujet': forms.Select(attrs={
                'class': 'form-control',
            }),
            'message': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Votre message...',
            }),
        }
        labels = {
            'prenom': 'Prénom *',
            'nom': 'Nom *',
            'email': 'Adresse email *',
            'telephone': 'Téléphone',
            'formation': 'Formation souhaitée',
            'sujet': 'Sujet *',
            'message': 'Message *',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Formations actives uniquement dans le select
        self.fields['formation'].queryset = Formation.objects.filter(actif=True)
        self.fields['formation'].empty_label = "-- Choisir une formation --"

        self.fields['telephone'].required = False
        self.fields['formation'].required = False


class InscriptionCompteForm(UserCreationForm):
    """Formulaire de création de compte étudiant."""

    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'placeholder': 'exemple@email.com',
        })
    )

    first_name = forms.CharField(
        max_length=100,
        required=True,
        label='Prénom',
        widget=forms.TextInput(attrs={
            'placeholder': 'Jean Raymond',
        })
    )

    last_name = forms.CharField(
        max_length=100,
        required=True,
        label='Nom',
        widget=forms.TextInput(attrs={
            'placeholder': 'BELONY',
        })
    )

    class Meta:
        model = User
        fields = [
            'first_name',
            'last_name',
            'username',
            'email',
            'password1',
            'password2',
        ]

        labels = {
            'username': "Nom d'utilisateur",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['username'].widget.attrs.update({
            'placeholder': 'jeanraymond',
        })

        self.fields['password1'].widget.attrs.update({
            'placeholder': '••••••••',
        })

        self.fields['password2'].widget.attrs.update({
            'placeholder': '••••••••',
        })

        self.fields['username'].help_text = (
            '150 caractères max. Lettres, chiffres et @/./+/-/_ uniquement.'
        )

        self.fields['password1'].help_text = (
            'Minimum 8 caractères.'
        )

        self.fields['password2'].help_text = (
            'Confirme ton mot de passe.'
        )


class ConnexionForm(AuthenticationForm):
    """Formulaire de connexion."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['username'].widget.attrs.update({
            'placeholder': "Nom d'utilisateur",
        })

        self.fields['password'].widget.attrs.update({
            'placeholder': '••••••••',
        })