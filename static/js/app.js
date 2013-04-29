$(function() {

    hideAddressBar();

    $('.add-meal').live('click', function(e) {
        e.preventDefault();
        $(this).after($('#meal-control').html());
        $('input[name="meal"]:last').focus();
        $(this).replaceWith($('#remove-control').html());
        // $(this).remove();
        // $('#meal-control').html()
    });

    $('.remove-meal').live('click', function(e) {
        e.preventDefault();
        $(this).prev().remove();
        $(this).remove();
    });
});

/*! Normalized address bar hiding for iOS & Android (c) @scottjehl MIT License */
function hideAddressBar() {

    var doc = window.document;

    // If there's a hash, or addEventListener is undefined, stop here
    if( !location.hash && window.addEventListener ){

        //scroll to 1
        window.scrollTo( 0, 1 );
        var scrollTop = 1,
            getScrollTop = function(){
                return window.pageYOffset || doc.compatMode === "CSS1Compat" && doc.documentElement.scrollTop || doc.body.scrollTop || 0;
            },

            //reset to 0 on bodyready, if needed
            bodycheck = setInterval(function(){
                if( doc.body ){
                    clearInterval( bodycheck );
                    scrollTop = getScrollTop();
                    window.scrollTo( 0, scrollTop === 1 ? 0 : 1 );
                }
            }, 15 );

        window.addEventListener( "load", function(){
            setTimeout(function(){
                //at load, if user hasn't scrolled more than 20 or so...
                if( getScrollTop() < 20 ){
                    //reset to hide addr bar at onload
                    window.scrollTo( 0, scrollTop === 1 ? 0 : 1 );
                }
            }, 0);
        }, false );
    }

}