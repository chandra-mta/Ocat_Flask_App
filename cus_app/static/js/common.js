<script>
    function WindowOpener(html) {
        msgWindow = open("","displayname","toolbar=no,directories=no,
                     menubar=no, location=no,scrollbars=yes,status=no,
                     width=1000,height=1500,resize=no");
        msgWindow.document.write("<html><body>");
        msgWindow.document.write("<iframe src=\'" + html + "\' border=0 width=980 height=1480>");
        msgWindow.document.write("</body></html>");
        msgWindow.document.close();
        msgWindow.resizeTo(1000, 1500);
        msgWindow.focus();
    }

    function ImageOpener(img) {
        imgWindow = open("", "displayname", "toolbar=no,directories=no,
                         menubar=no, location=no,scrollbars=yes,status=no,
                         width=700, height=700, resize=no");
        imgWindow.document.write("<html><body><title>sky map</title>");
        imgWindow.document.write("<img src=\'" + img + "\' border=0>");
        imgWindow.document.write("</body></html>");
        imgWindow.document.close();
        imgWindow.resizeTo(700, 700);
        imgWindow.focus();
    }

</script>

