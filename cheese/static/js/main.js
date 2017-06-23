jQuery(function($) {
  $(".pop").on("click", function() {
    // Get the image src and convert the thumbnail URL.
    var src = $(this).find('img').attr('src');
    src = src.replace('/static/images/thumbs', '');
    var regex = /(.*)_\d+x\d+_\d+\.(.*)/;
    src = src.replace(regex, '$1.$2')
    $('#imagepreview').attr('src', src);
    // Set the alt text.
    var alt_text = $(this).find('img').attr('alt');
    if (alt_text == null) {
      $('#imagepreview-caption').text('');
    } else {
      $('#imagepreview-caption').text(alt_text);
    }
    $('#imagemodal').modal('show');
  });
});
