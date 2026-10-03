from django import forms


class UploadDatasetForm(forms.Form):
    dataset = forms.FileField(
        label="File CSV",
        help_text="Massimo 5 MB. Colonne richieste: transaction_id, date, amount, vendor, country, approved_by, category.",
        widget=forms.ClearableFileInput(attrs={"accept": ".csv,text/csv"}),
    )
