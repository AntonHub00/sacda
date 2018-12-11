$(document).ready(function(){
  $('#my-p-s-form').on('submit', function(event){
    $.ajax({
      data : {
        name : $('#name').val(),
        first_last_name: $('#first_last_name').val(),
        second_last_name : $('#second_last_name').val(),
        rfc : $('#rfc').val(),
        email : $('#email').val(),
        phone : $('#phone').val(),
        job : $('#job').val(),
        entry_time : $('#entry_time').val(),
        exit_time : $('#exit_time').val(),
        place : $('#place').val(),
        password : $('#password').val()
      },
      type : 'POST',
      url : '/administrador/profesionales/alta'
    })
    .done(function(data){
      if (data.error){
        $('#my-p-s-error-message').text(data.error).show();
      }
      else{
        alert(data.success);
        window.location.href = data.new_url;
      }
    });

    event.preventDefault();
  });
});

