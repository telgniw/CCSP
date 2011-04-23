/*!
 * Using jQuery Javascript Library v1.5.1.
 */
$('#bar').ready(
    function() {
        $.get('/query', {
            city: 'Taipei'
        }, function(data) {
            xml = $.parseXML(data);
            $('#date').html(
                $(xml).find('current_date_time').attr('data').split(' ')[0]
            );
            $('#city').html(
                $(xml).find('city').attr('data')
            );
            $('#temperature').html(
                $(xml).find('temp_c').attr('data') + '&deg;C'
            );
            $('#condition').html(
                $(xml).find('condition').attr('data')
            );
        })
    }
);
$('body').ready(
    function() {
        if($.browser.mozilla) {
            $('body').css('color', 'pink');
        }
        else {
            $('body').css('color', 'gray');
        }
    }
);
$(document).ready(
    function() {
        $('.delete').click(
            function() {
                var id = $(this).attr('id');
                $.post('/delete', {
                    key: id
                }, function() {
                    var target = '#message_' + id;
                    $(target).fadeOut(400, function() {
                        $(target).detach();
                    });
                });
            }
        );
    }
);