// jQuery scripts for the site
$(function () {

    // Navigation Menu Drop-Down
    $("#navToggle").on('click tap', function () {
        $("#navContainer").slideToggle("0.5s");
    });


    // Small screen drawers close and open
    $("#browseToggle").click(function () {
        $(this).children("span").toggleClass("rotate");
        $(".browseDrawer").slideToggle("0.5s");
    });

    /************* JUNE 4 ******************/
    /************* MELISSA ****************/
    // Hamburger menu animation
    $("#navToggle").click(function () {
        $(this).toggleClass("active");
    });


    // Notice dropdown menu expand and collapse
    $('.noticeWrapper').click(function () {
        // $(this).children('#notificationBox').toggleClass('noticeCollapse noticeExpand');
        $(this).children('#notificationBox').slideToggle('0.5s');
    });
});



