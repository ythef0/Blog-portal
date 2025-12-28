/* static/admin/js/meme_deletion.js */
(function($) {
    $(document).ready(function() {
        // Add select all/none functionality for memes
        const selectAllMemeButton = $('<button type="button" id="select-all-memes" style="margin-bottom: 10px;">Избери всички мемета</button>');
        const memeForm = $('form[method="post"]').has('input[name="delete_selected_memes"]');
        if(memeForm.length > 0) {
            memeForm.find('div[style="max-height: 400px; overflow-y: auto; margin-bottom: 10px;"]').before(selectAllMemeButton);
        }

        $('#select-all-memes').click(function() {
            const checkboxes = memeForm.find('input[type="checkbox"][name*="memes_meme_"]');
            checkboxes.prop('checked', !checkboxes.first().prop('checked'));
        });

        // Add counter for selected memes
        const memeCounter = $('<div id="selected-meme-count" style="margin-top: 5px; font-weight: bold;">Избрани мемета: 0</div>');
        memeForm.find('.submit-row').prepend(memeCounter);

        memeForm.find('input[type="checkbox"][name*="memes_meme_"]').change(function() {
            const selectedCount = memeForm.find('input[type="checkbox"][name*="memes_meme_"]:checked').length;
            $('#selected-meme-count').text('Избрани мемета: ' + selectedCount);
        });

        // Add select all/none functionality for song suggestions
        const selectAllSuggestionButton = $('<button type="button" id="select-all-suggestions" style="margin-bottom: 10px;">Избери всички предложения</button>');
        const suggestionForm = $('form[method="post"]').has('input[name="delete_selected_suggestions"]');
        if(suggestionForm.length > 0) {
            suggestionForm.find('div[style="max-height: 400px; overflow-y: auto; margin-bottom: 10px;"]').before(selectAllSuggestionButton);
        }

        $('#select-all-suggestions').click(function() {
            const checkboxes = suggestionForm.find('input[type="checkbox"][name*="suggestions_suggestion_"]');
            checkboxes.prop('checked', !checkboxes.first().prop('checked'));
        });

        // Add counter for selected suggestions
        const suggestionCounter = $('<div id="selected-suggestion-count" style="margin-top: 5px; font-weight: bold;">Избрани предложения: 0</div>');
        suggestionForm.find('.submit-row').prepend(suggestionCounter);

        suggestionForm.find('input[type="checkbox"][name*="suggestions_suggestion_"]').change(function() {
            const selectedCount = suggestionForm.find('input[type="checkbox"][name*="suggestions_suggestion_"]:checked').length;
            $('#selected-suggestion-count').text('Избрани предложения: ' + selectedCount);
        });

        // Add select all/none functionality for poll questions
        const selectAllPollButton = $('<button type="button" id="select-all-polls" style="margin-bottom: 10px;">Избери всички анкети</button>');
        const pollForm = $('form[method="post"]').has('input[name="delete_selected_polls"]');
        if(pollForm.length > 0) {
            pollForm.find('div[style="max-height: 400px; overflow-y: auto; margin-bottom: 10px;"]').before(selectAllPollButton);
        }

        $('#select-all-polls').click(function() {
            const checkboxes = pollForm.find('input[type="checkbox"][name*="polls_poll_"]');
            checkboxes.prop('checked', !checkboxes.first().prop('checked'));
        });

        // Add counter for selected polls
        const pollCounter = $('<div id="selected-poll-count" style="margin-top: 5px; font-weight: bold;">Избрани анкети: 0</div>');
        pollForm.find('.submit-row').prepend(pollCounter);

        pollForm.find('input[type="checkbox"][name*="polls_poll_"]').change(function() {
            const selectedCount = pollForm.find('input[type="checkbox"][name*="polls_poll_"]:checked').length;
            $('#selected-poll-count').text('Избрани анкети: ' + selectedCount);
        });
    });
})(django.jQuery);