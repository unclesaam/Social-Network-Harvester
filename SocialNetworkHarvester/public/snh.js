var iDisplayLength = 100
var sPaginationType = "full_numbers";
var sDom = 'Tp<"clear">lfrtip';
var aaSorting = [[ 0, "desc" ]];
var bAutoWidth = false
var bServerSide = true; 
var aoColumnDefs = [ 
    { 
        "bSearchable": false, "aTargets": [ 0 ],
    }
];


function _wordwrap($text, $size){
    $size = typeof $size !== 'undefined' ? $size : 10;
    final = "";
    var re = new RegExp(".{1,"+$size+"}","g");
    splitted = $text.match(re);
    for (i in splitted){
        final += splitted[i] + "&#8203;"
    }
    return final;
}

TableTools.BUTTONS.download = {
    "sAction": "text",
    "sFieldBoundary": "",
    "sFieldSeperator": "\t",
    "sNewLine": "<br>",
    "sToolTip": "Download csv",
    "sButtonClass": "DTTT_button_csv",
    "sButtonClassHover": "DTTT_button_csv_hover",
    "sButtonText": "Download",
    "mColumns": "all",
    "bHeader": true,
    "bFooter": true,
    "sDiv": "",
    "fnMouseover": null,
    "fnMouseout": null,
    "fnClick": function( nButton, oConfig ) {
        var oParams = this.s.dt.oApi._fnAjaxParameters( this.s.dt );
        var iframe = document.createElement('iframe');
        iframe.style.height = "0px";
        iframe.style.width = "0px";
        iframe.src = oConfig.sUrl+"?"+$.param(oParams);
        document.body.appendChild( iframe );
     },
    "fnSelect": null,
    "fnComplete": null,
    "fnInit": null,
    "sButtonText": "CSV",
    "sSwfPath": "/static/swf/copy_cvs_xls_pdf.swf",

};



