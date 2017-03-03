$(document).ready(function() {

  $("#update_profile").click(function () {
    var data = {}

    data["username"] = $("#username").val();
    data["email"] = $("#email").val();
    data["phone"] = $("#phone").val();
    data["street"] = $("#street").val();
    data["apt_number"] = $("#apt_number").val();
    data["city"] = $("#city").val();
    data["zip"] = $("#zip").val();
    data["state"] = $("#state").val();

    if ($("#first_name")) {
      data['first_name'] = $("#first_name").val();
    }

    if ($("#last_name")) {
      data['last_name'] = $("#last_name").val();
    }

    console.log(JSON.stringify(data));
    $.getJSON($SCRIPT_ROOT + '/update_profile', {
      data: JSON.stringify(data),
    }, function(data) {
      $('#profile_mascot_block').removeAttr("style");
      $('#profile_mascot_message').text("Successfully updated profile");
    });
  });

})
