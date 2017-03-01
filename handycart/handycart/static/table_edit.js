$(document).ready(function() {
  var $TABLE = $('#table');
  var $BTN = $('#export-btn');
  var $EXPORT = $('#export');

  // hide a row from the table

  $('#table-add').click(function () {
    var $clone = $TABLE.find('tr.hide').clone(true).removeClass('hide table-line');
    $clone.removeAttr("style");
    console.log($clone);
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

  $BTN.click(function () {
    var $rows = $TABLE.find('tr:not(:hidden)');
    var headers = [];
    var data = [];

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
    $EXPORT.text(JSON.stringify(data));
  });
})
