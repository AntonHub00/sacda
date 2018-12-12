$(document).ready(function(){
  $('#my-s-s-form').on('submit', function(event){
    $.ajax({
      data : {
        name : $('#name').val(),
        first_last_name : $('#first_last_name').val(),
        second_last_name : $('#second_last_name').val(),
        enrollment : $('#enrollment').val(),
        email : $('#email').val(),
        phone : $('#phone').val(),
        career : $('#career').val(),
        gender : $('#gender').val(),
        semester : $('#semester').val(),
        password : $('#password').val(),
        name_tutor : $('#name_tutor').val(),
        place : $('#place').val(),
        first_last_name_tutor : $('#first_last_name_tutor').val(),
        second_last_name_tutor : $('#second_last_name_tutor').val(),
        phone_tutor : $('#phone_tutor').val(),
        email_tutor : $('#email_tutor').val()
      },
      type : 'POST',
      url : '/registrarme'
    })
    .done(function(data){
      if (data.error){
        $('#my-s-s-error-message').text(data.error).show();
      }
      else{
        alert(data.success);
        window.location.href = data.new_url;
      }
    });

    event.preventDefault();
  });
});


