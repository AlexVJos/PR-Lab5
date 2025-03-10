from django import forms

class EmailTaskForm(forms.Form):
    recipient = forms.EmailField(
        label="Recipient Email",
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email address'})
    )
    subject = forms.CharField(
        max_length=100,
        label="Subject",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Email subject'})
    )
    message = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': 'Email message'}),
        label="Message"
    )
    attach_task_details = forms.BooleanField(
        required=False,
        initial=True,
        label="Attach task details",
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )