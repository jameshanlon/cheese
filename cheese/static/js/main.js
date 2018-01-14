jQuery(function($) {
  // Add a search function to survey select box.
  $("#submit-results-form #survey").chosen();
  // Add date picker to form fields.
  $('[id="datetimepicker"]').datetimepicker({format: 'DD/MM/YYYY'});
});
