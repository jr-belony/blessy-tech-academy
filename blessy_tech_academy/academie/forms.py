from django import forms
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