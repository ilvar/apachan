$(function() {
//  var largePicDelay=1000, largePicTimeout;
//  $('img.media-object[href]').on('mousemove', function(eventObject) {
//    $this = $(this);
//    imgY = eventObject.clientY + 10;
//    imgY = Math.min(imgY, top.innerHeight - 600);
//
//    largePicTimeout = setTimeout(function(){
//      $("img.pic-preview").prop("src", $this.attr("href")).css({
//        top: imgY,
//        left: eventObject.clientX + 10,
//      }).fadeIn();
//    }, $("img.pic-preview").is(":visible") && 1 || largePicDelay);
//  });
//
//  $("img.media-object[href]").mouseleave(function() {
//     clearTimeout(largePicTimeout);
//     $("img.pic-preview").fadeOut();
//  });

  fbOptions = {
		fitToView	: true,
		autoSize : false,
		autoHeight	: true,
		closeClick	: false,
		openEffect	: 'none',
		closeEffect	: 'none'
	};

  $('.post-toggle, .comment-reply').fancybox(fbOptions);

  if ($('.post-form').find('.alert-danger, .has-success, .has-error').length == 0) {
    $("#post_form_fancybox").hide();
  } else {
    $.fancybox('#post_form_fancybox', fbOptions);
  }

  $("a.link-enlarge").click(function() {
    $(this).parents('.pic-full').toggleClass('container');
    return false;
  });

  $('#night_toggle').click(function() {
    top.location = top.location.href + "?toggle_night=1"
  });

  $('.dropdown-toggle').click(function() {
    $(this).parents('li').first().toggleClass('open');
  });

  $('.navbar input[type=checkbox]').change(function() {
    $('.save-feeds').show();
  });

  $('.save-feeds').hide();

  $('.show-hidden').click(function() {
    $(this).parents('.panel').find('.post-hidden').removeClass('post-hidden');
    $(this).parents('.panel-heading').hide();
    return false;
  });

  $(".captcha-answers input").change(function() {
    $form = $(this).parents("form");
    setTimeout(function() {
      $form.submit();
    }, 10);
  });

  $(".panel-moderation form button[value^=delete]").click(function() {
    $form = $(this).parents("form");
    token = $form.find("input[name=csrfmiddlewaretoken]").val();
    $.post($form.attr("action"), {"action": this.value, "csrfmiddlewaretoken": token}, function() {
      $form.parents('.panel-default,.panel-success').removeClass('panel-success').removeClass('panel-default').addClass('panel-danger');
    });
    return false;
  });

  $(".comment-reply").click(function() {
    $(".post-form #id_parent").val($(this).data("comment"));
  });

  $(".post-toggle").click(function() {
    $(".post-form #id_parent").val("");
  });

  $('.form-dislike button').click(function() {
    $(this).parents('form').find('input[name=action]').val($(this).val());
  });

  $('.form-dislike').submit(function() {
    $this = $(this);
    $post = $this.parents('.panel-post');
    $.post($this.attr('action'), $this.serialize(), function() {
      $post.children().addClass('post-hidden');
      $post.children(':first').before('<div class="panel-heading"><a name="comment"></a>Вы спрятали этот пост. <a href="#" class="show-hidden">Показать</a></div>');
    });
    return false;
  });

});