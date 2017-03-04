$(document).ready(function() {
  var $TABLE = $('#table');
  var $BTN = $('#export');

  // hide a row from the table

  $('#table-add').click(function () {
    var $clone = $TABLE.find('tr.hide').clone(true).removeClass('hide table-line');
    $clone.removeAttr("style");
    $TABLE.find('table').append($clone);
  });

  $('.table-remove').click(function () {
    $(this).parents('tr').detach();
  });

  $('td').click(function () {
    if ($(this).text() == "Enter Qty" || $(this).text() == "Enter Price") {
      $(this).text("");
    }
  });

  // A few jQuery helpers for exporting only
  jQuery.fn.pop = [].pop;
  jQuery.fn.shift = [].shift;

  var data = [];
  $BTN.click(function () {
    console.log("Button clicked");
    var $rows = $TABLE.find('tr:not(:hidden)');
    var headers = [];


    // Get the headers (add special header logic here)
    $($rows.shift()).find('th:not(:empty)').each(function () {
      headers.push($(this).text().toLowerCase());
    });

    // Turn all existing rows into a loopable array
    $rows.each(function () {
      var $td = $(this).find('td');
      var h = {};

      // Use the headers from earlier to name our hash keys
      headers.forEach(function (header, i) {
        if (header != "add") {
            h[header] = $td.eq(i).text();
        }
      });

      data.push(h);
    });

    // Output the result
    console.log(JSON.stringify(data));
    console.log("PRODUCT ID " + $("#product_id").val());

    $.getJSON($SCRIPT_ROOT + '/add_product_properties', {
      properties: JSON.stringify(data),
      product_id: $("#product_id").val()
    }, function(data) {
      $('#product_properties_mascot_block').removeAttr("style");
      $('#product_properties_mascot_message').text("Successfully updated product info");
    });

  });
})
