# blog/forms.py
from django import forms
from django.utils.safestring import mark_safe
from .models import MemeOfWeek, BellSongSuggestion, PollQuestion

class MemeSelectionForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Get all memes (or limit to recent ones)
        memes = MemeOfWeek.objects.all().order_by('-created_at')

        # Create a checkbox field for each meme
        for meme in memes:
            field_name = f'meme_{meme.id}'
            image_preview = f'<img src="{meme.image.url}" style="width: 50px; height: 50px; margin-right: 10px; object-fit: cover;" onerror="this.style.display=\'none\'">' if meme.image else ''
            title = meme.title or f"Meme by {meme.user.username}"
            status_text = "Одобрено" if meme.is_approved else "Неодобрено"
            date_text = meme.created_at.strftime('%d.%m.%Y') if meme.created_at else "Без дата"
            votes_text = f" | Гласове: {meme.votes}" if meme.votes else ""

            self.fields[field_name] = forms.BooleanField(
                required=False,
                label=mark_safe(f'{image_preview}{title} <span class="status-{"approved" if meme.is_approved else "not-approved"}">[{status_text}]</span> | {date_text}{votes_text}'),
                widget=forms.CheckboxInput(attrs={'data-meme-id': meme.id})
            )

    def delete_selected_memes(self):
        """Delete the selected memes"""
        deleted_count = 0
        for field_name, value in self.cleaned_data.items():
            if value and field_name.startswith('meme_'):
                meme_id = field_name.replace('meme_', '')
                try:
                    meme = MemeOfWeek.objects.get(id=meme_id)
                    meme.delete()
                    deleted_count += 1
                except MemeOfWeek.DoesNotExist:
                    continue
        return deleted_count


class SongSuggestionSelectionForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Get all song suggestions (or limit to recent ones)
        suggestions = BellSongSuggestion.objects.all().order_by('-submitted_at')

        # Create a checkbox field for each suggestion
        for suggestion in suggestions:
            field_name = f'suggestion_{suggestion.id}'
            title = suggestion.title
            status_text = suggestion.get_status_display()
            date_text = suggestion.submitted_at.strftime('%d.%m.%Y') if suggestion.submitted_at else "Без дата"
            votes_text = f" | Гласове: {suggestion.votes}" if suggestion.votes else ""
            slot_text = f" | Слот: {suggestion.get_slot_display()}"

            self.fields[field_name] = forms.BooleanField(
                required=False,
                label=f'{title} [{status_text}]{slot_text} | {date_text}{votes_text}',
                widget=forms.CheckboxInput(attrs={'data-suggestion-id': suggestion.id})
            )

    def delete_selected_suggestions(self):
        """Delete the selected song suggestions"""
        deleted_count = 0
        for field_name, value in self.cleaned_data.items():
            if value and field_name.startswith('suggestion_'):
                suggestion_id = field_name.replace('suggestion_', '')
                try:
                    suggestion = BellSongSuggestion.objects.get(id=suggestion_id)
                    suggestion.delete()
                    deleted_count += 1
                except BellSongSuggestion.DoesNotExist:
                    continue
        return deleted_count


class PollQuestionSelectionForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Get all poll questions (or limit to recent ones)
        polls = PollQuestion.objects.all().order_by('-created_at')

        # Create a checkbox field for each poll
        for poll in polls:
            field_name = f'poll_{poll.id}'
            title = poll.title
            start_date = poll.start_date.strftime('%d.%m.%Y') if poll.start_date else "Без дата"
            end_date = poll.end_date.strftime('%d.%m.%Y') if poll.end_date else "Без дата"

            self.fields[field_name] = forms.BooleanField(
                required=False,
                label=f'{title} | Начало: {start_date} | Край: {end_date}',
                widget=forms.CheckboxInput(attrs={'data-poll-id': poll.id})
            )

    def delete_selected_polls(self):
        """Delete the selected poll questions"""
        deleted_count = 0
        for field_name, value in self.cleaned_data.items():
            if value and field_name.startswith('poll_'):
                poll_id = field_name.replace('poll_', '')
                try:
                    poll = PollQuestion.objects.get(id=poll_id)
                    poll.delete()
                    deleted_count += 1
                except PollQuestion.DoesNotExist:
                    continue
        return deleted_count