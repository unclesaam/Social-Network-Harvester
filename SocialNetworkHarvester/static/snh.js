var iDisplayLength = 10
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


lastMenuItemClicked = null;
$(document).ready(function(){
    $('.dropdown').click(function(elem){
        $('.menu-selection').removeClass('menu-selection')
        $(elem.currentTarget).addClass('menu-selection')
        if($('#submenu').css('display') != 'none' && elem.currentTarget === lastMenuItemClicked){
            $('#submenu').hide();
        } else {
            displayHarvesters(elem.currentTarget.getAttribute('l'));
            lastMenuItemClicked = elem.currentTarget;
        }
    })
})

function displayHarvesters(type){
    html = '<td class="menu-selection" colspan=6><table class="tableheader"><tr>'

    $.ajax({
        method:'GET',
        url:'/getHarvs',
        data:{
            'platform':type
        },
        success:function(response){
            html += '<td><a href="' + response['All data'] + '">All data</a></td>';
            delete response['All data']
            Object.keys(response).forEach(function(name){
                html += '<td><a href="'+response[name]+'">'+name+'</a></td>'
            })
            html += '</tr></table></td>'
            $('#submenu').html(html);
            $('#submenu').show();
        }
    })
}