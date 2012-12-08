from django.core.exceptions import ValidationError, PermissionDenied
from django import forms

import helper

class UploadForm(forms.Form):
    file  = forms.FileField()
    # Don't show user field


class BrowseSettingsColumnsForm(forms.Form):
    # provide a multiple select field
    columns = forms.MultipleChoiceField(
                widget=forms.CheckboxSelectMultiple,
                label=""
                )

    def __init__(self, *args, **kwargs):

        if "columns" in kwargs:
            # binding form (for presenting initial data)
            columns = kwargs.pop("columns")
        else:
            columns = None
        super(BrowseSettingsColumnsForm, self).__init__(*args, **kwargs)

        self.text = "my form text"

        # populate multiple select field (which fields to display)
        self.fields["columns"].choices = [(i["order"], i["name"]) for i in helper.DEFAULT_BROWSE_COLUMNS_AVAILABLE]

        if columns != None:
            # pre-select the multiple select field (populate fields with data from db)
            tmp = []
            for i in columns:
                if i["show"]:
                    tmp.append(i["order"])
            self.fields["columns"].initial = tmp
        # else: the data from request.POST will fill in initial data


    def save(self, user_status, commit=True):
        tmp = helper.DEFAULT_BROWSE_COLUMNS_AVAILABLE

        # set all columns to false
        for col in tmp:
            col["show"] = False

        # enable only transmitted columns
        for item in self.cleaned_data["columns"]:
            for col in tmp:
                if col["order"] == item:
                    col["show"] = True

        user_status.set("browse_column_display", tmp)

"""
Thanks to
http://ontehfritz.wordpress.com/2009/02/15/django-forms-choicefield-and-multiplechoicefield/

class QuestionMulipleSelect(forms.Form):
    answers = forms.MultipleChoiceField(widget=forms.CheckboxSelectMultiple, label="")
.


def render_questions(request):
.
.  Some code here 
.

   if request.method == 'POST':
        form_list = create_question_forms(request.POST)

        for form in form_list:
            if form.is_valid():
                form.save()
            
        return HttpResponseRedirect(some_url) #direct to url after
    else:
            form_list = create_question_forms()

    return render_to_response('your_template.html', {'forms': form_list})

the request.POST on submit contains a QueryDict object that contains all of your submitted data, so pass this to your create_question_forms object, which is defined like this:

def create_question_forms(data=None):
    question_list = ... # get all your questions from here via db or where ever your questions are stored
    form_list = []
   
   for pos, question in enumerate(question_list):
            #data is the request.POST and if it is there will populate you questions with the user choices
            form_list.append(QuestionMulipleChoiceRadio(question, data, prefix=pos))

    return form_list

Then your Question form would be something like this:

class QuestionCheckBox(forms.Form):
    answers = forms.MultipleChoiceField(widget=forms.CheckboxSelectMultiple, label="")
    def __init__(self, question, *args, **kwargs):
        super(QuestionCheckBox, self).__init__(*args, **kwargs)
        self.text = question.text
        self.question = question
     
        answers = question.answer_set.all().order_by('index')
        self.fields['answers'].choices = [(str(i), a.text) for i, a in enumerate(answers)]
        self.choices_dict = dict(self.fields['answers'].choices)
        self.count = count

    def save(self, commit=True):
      ...
      Some more code, do what you want
      ....
"""