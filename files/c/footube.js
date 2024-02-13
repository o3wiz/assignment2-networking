var counter = 0;

//$(document).ready(function(){
$(function(){
    $('.card').hover(function(){       
        $(this).addClass('videoOn');

    },function(){
        $(this).removeClass('videoOn');
    });

    $('.card').click(function(){
        $('img',this).css('visibility','visible');
        
        const img1 = $('img',this).attr("src");
        const img2 = $('img',this).attr("src");

        counter++;

        if (counter == 2){
            counter = 0;
        }

        console.log(counter);
    });

    $('.row').sortable();

    var availableTags = [
        "aaa",
        "bbb",
        "ccc"
      ];

    $( ".search" ).autocomplete({
        source: availableTags
      });
});