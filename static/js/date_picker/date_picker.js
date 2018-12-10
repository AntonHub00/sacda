$('#date-picker').datepicker({
    beforeShowDay: function(date){
      var day = date.getDay();
      return [(day != 0 && day != 6)];
    },
    format: 'dd/mm/yyyy',
    language: 'es',
    daysOfWeekDisabled: [0,6],
    autoclose: true,
    todayHighlight: true,
    startDate: '0d',
    endDate: '+16d'
});
