$(document).ready(function () {
    var result_element = $('.result_frame');
    result_element.load(function () {
        $(this).height($(document).height());
        $(this).width($(document).width());
    });
});

function show_frame(combination) {
    $('.result_div').hide();
    $('#' + combination).show();
}