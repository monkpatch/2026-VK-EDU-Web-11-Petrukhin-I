(function ($) {
  function csrfToken() {
    var match = document.cookie.match(/(?:^|; )csrftoken=([^;]+)/);
    return match ? decodeURIComponent(match[1]) : '';
  }

  function showAjaxError(xhr) {
    var error = (xhr.responseJSON && xhr.responseJSON.error) || 'request_failed';
    if (error === 'auth_required') {
      window.location.href = window.askPupkinAjax.loginUrl;
      return;
    }
    if (window.showAskPupkinToast) {
      window.showAskPupkinToast('Ошибка: ' + error, 'danger');
    }
  }

  function setVoteButtons($widget, vote) {
    $widget.attr('data-like-state', vote);
    $widget.find('.btn-up').prop('disabled', vote === 'up');
    $widget.find('.btn-down').prop('disabled', vote === 'down');
  }

  function sendVote($widget, type) {
    var kind = $widget.data('vote-kind');
    var url = kind === 'answer' ? window.askPupkinAjax.answerVoteUrl : window.askPupkinAjax.questionVoteUrl;
    $widget.find('button').prop('disabled', true);
    $.ajax({
      url: url,
      method: 'POST',
      contentType: 'application/json',
      dataType: 'json',
      headers: {'X-CSRFToken': csrfToken()},
      data: JSON.stringify({id: $widget.data('object-id'), type: type})
    }).done(function (data) {
      $widget.find('.vote-count').text(data.rating);
      setVoteButtons($widget, data.vote);
    }).fail(function (xhr) {
      showAjaxError(xhr);
      setVoteButtons($widget, $widget.attr('data-like-state') || 'none');
    });
  }

  $(document).on('click', '.vote-widget .btn-up:not(:disabled)', function () {
    sendVote($(this).closest('.vote-widget'), 'like');
  });

  $(document).on('click', '.vote-widget .btn-down:not(:disabled)', function () {
    sendVote($(this).closest('.vote-widget'), 'dislike');
  });

  $(document).on('change', '.correct-answer-toggle', function () {
    var $checkbox = $(this);
    if (!$checkbox.prop('checked')) {
      $checkbox.prop('checked', true);
      return;
    }
    $.ajax({
      url: window.askPupkinAjax.answerCorrectUrl,
      method: 'POST',
      contentType: 'application/json',
      dataType: 'json',
      headers: {'X-CSRFToken': csrfToken()},
      data: JSON.stringify({
        question_id: $checkbox.data('question-id'),
        answer_id: $checkbox.data('answer-id')
      })
    }).done(function (data) {
      $('.correct-answer-toggle').prop('checked', false).prop('disabled', false)
        .closest('.answer-card').removeClass('border-success');
      var $current = $('.correct-answer-toggle[data-answer-id="' + data.answer_id + '"]');
      $current.prop('checked', true).prop('disabled', true).closest('.answer-card').addClass('border-success');
    }).fail(function (xhr) {
      $checkbox.prop('checked', false);
      showAjaxError(xhr);
    });
  });
})(jQuery);
