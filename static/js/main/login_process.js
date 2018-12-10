$(document).ready(function(){
  $('#my-login-form').on('submit', function(event){
    $.ajax({
      data : {
        user : $('#user').val(),
        password : $('#password').val()
      },
      type : 'POST',
      url : '/login'
    })
    .done(function(data){
      if (data.error){
        $('#my-error-message').text(data.error).show();
      }
      else{
        window.location.href = data.new_url;
      }
    });

    event.preventDefault();
  });
});
