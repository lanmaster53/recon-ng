$("#workspace").change(function(){
    // reset the view
    $("#reports").hide();
    $("#tables").hide();
    $("#summary").hide();
    $("#columns").hide();
    $("#exports").hide();
    $("#data").hide();
    var workspace = $("#workspace option:selected").text();
    // set the workspace
    $.ajax({
        type: "PATCH",
        url: "/api/workspaces/"+workspace,
        data: JSON.stringify({"status": "active"}),
        processData: false,
        contentType: 'application/json',
    })
    .done(function(data, status){
        console.log("Workspace activated: "+workspace);
    });
    // create the summary
    $.get("/api/dashboard", function(data, status){
        createSummary(data);
    });
    // create the workspace
    $.get("/api/tables/", function(data, status){
        createWorkspace(data.tables);
    });
    // create the reports options
    $.get("/api/reports/", function(data, status){
        createReports(data.reports);
    });
    // show the new elements on screen
    $("#reports").show();
    $("#tables").show();
    $("#summary").show();
    // set the width of the workspace select box
    //setSelectWidth($(this));
    // set the height of the summary panels
    setFillHeight();
});

$("#reports-list").on("click", "li", function(e) {
    // get the report name
    var report = $(e.target).text();
    // open in a new tab
    window.open("/api/reports/"+report, '_blank');
    // prevent the checked state
    e.preventDefault();
    e.stopPropagation();
});

$("#tables-list").on("click", "li", function() {
    // reset the previously selected table style
    $("#tables-list > li").each(function (i, e) {
        $(e).removeClass("active");
    });
    $(this).addClass("active");
    // get the data from the api
    var table = $(this).text();
    $.get("/api/tables/"+table, function(data, status) {
        // create the column filter
        createColumnFilter(data.columns);
        // create the data table
        createDataTable(data.rows);
    });
    $.get("/api/exports", function(data, status) {
        // create the export menu
        createExportMenu(data.exports);
    });
    // show the new elements on screen
    $("#summary").hide();
    $("#columns").show();
    $("#exports").show();
    $("#data").show();
});

$("#columns-list").on("click", "#filter", function (e) {
    // build the columns parameter value
    var checked = [];
    $("input[name='column']:checked").each(function() {
        checked.push($(this).val());
    });
    var checkedStr = checked.join();
    // get the current table
    var table = "";
    $("#tables-list > li").each(function (i, e) {
        if ($(e).hasClass("active")) {
            table = $(e).find('a').text();
        }
    });
    // get the data from the api
    $.get("/api/tables/"+table+"?columns="+checkedStr, function(data, status) {
        // create the data table
        createDataTable(data.rows);
    });
    // show the new elements on screen
    $("#data").show();
    // prevent the checked state
    e.preventDefault();
    e.stopPropagation();
});

$("#exports-list").on("click", "li", function(e) {
    // build the columns parameter value
    var checked = [];
    $("input[name='column']:checked").each(function() {
        checked.push($(this).val());
    });
    var checkedStr = checked.join();
    // get the current table
    var table = "";
    $("#tables-list > li").each(function (i, e) {
        if ($(e).hasClass("active")) {
            table = $(e).find('a').text();
        }
    });
    // get the desired format
    var format = $(this).text();
    // open in a new tab to download the file
    window.open("/api/tables/"+table+"?format="+format+"&columns="+checkedStr, '_blank');
    // prevent the checked state
    e.preventDefault();
    e.stopPropagation();
});

function createWorkspace(tables) {
    // clear existing elements
    $("#tables-list").empty();
    // add DOM elements based on the provided table names
    $.each(tables, function(i) {
        var li = $("<li/>").appendTo($("#tables-list"));
        var a = $("<a/>").attr("href", "javascript:void(0)").text(tables[i]).appendTo(li);
    });
}

function createSummary(summary) {
    // clear existing elements
    $("#summary-list-l").empty();
    $("#summary-list-r").empty();
    // add DOM elements to left panel based on the provided records
    $.each(summary.records, function(i) {
        var div1 = $("<div/>").addClass("name").appendTo($("#summary-list-l")).text(summary.records[i].name);
        var div2 = $("<div/>").addClass("count").appendTo($("#summary-list-l")).text(summary.records[i].count);
    });
    // add DOM elements to right panel based on the provided modules
    if (summary.activity.length > 0) {
        $.each(summary.activity, function(i) {
            var div0 = $("<div/>").appendTo($("#summary-list-r"))
            var div1 = $("<div/>").addClass("module").appendTo(div0).text(summary.activity[i].module);
            var div2 = $("<div/>").addClass("runs").appendTo(div0).text(summary.activity[i].runs);
        });
    } else {
        $("#summary-list-r").append("<h5>No Data.</h5>");
    }
}

function createReports(reports) {
    // clear existing elements
    $("#reports-list").empty();
    // add DOM elements based on the provided report names
    $.each(reports, function(i) {
        var li = $("<li/>").appendTo($("#reports-list"));
        var a = $("<a/>").attr("href", "javascript:void(0)").text(reports[i]).appendTo(li);
    });
}

function createColumnFilter(columns) {
    // clear existing elements
    $("#columns-list").empty();
    // add DOM elements based on the provided column names
    $("#columns-list").append('<div class="label">Fields:</div>');
    $.each(columns, function(i, v) {
        var div = $("<div/>").addClass("ck-button").appendTo($("#columns-list"));
        var label = $("<label/>").appendTo(div);
        var input = $("<input/>", {type: "checkbox", name: "column", value: v, checked: true}).appendTo(label);
        var span = $("<span/>").addClass("no-select").text(v).appendTo(label);
    });
    $("#columns-list").append('<div class="ck-button ck-filter"><label><input type="checkbox" id="filter"><span class="no-select">filter</span></label></div>');
}

function createExportMenu(exports) {
    // clear existing elements
    $("#exports-list").empty();
    // add DOM elements based on the provided export names
    $.each(exports, function(i, v) {
        var li = $("<li/>").appendTo($("#exports-list"));
        var a = $("<a/>").attr("href", "javascript:void(0)").text(v).appendTo(li);
    });
}

function createDataTable(rows) {
    // clear existing elements
    $("#data-table").empty();
    // add DOM elements based on the provided rows
    if (rows.length > 0) {
        var table = $("<table/>", {id: "sorttable"}).addClass("sortable").addClass("center").appendTo($("#data-table"));
        // build the table header
        var thead = $("<thead/>").appendTo(table);
        var tr = $("<tr/>").appendTo(thead);
        $.each(rows[0], function(i, v) {
            var th = $("<th/>").addClass("no-select").text(i).appendTo(tr);
        });
        // build the table body
        var tbody = $("<tbody/>").appendTo(table);
        $.each(rows, function(i, row) {
            var tr = $("<tr/>").appendTo(tbody);
            $.each(row, function(i, v) {
                var td = $("<td/>").text(v).appendTo(tr);
            });
        });
        sorttable.makeSortable($("#sorttable")[0]);
    } else {
        $("#data-table").append("<h5>No Data.</h5>");
    }
}

function setSelectWidth(select) {
    $("#templateOption").text(select.val());
    // for some reason, a small fudge factor may be needed
    // so that the text doesn't become clipped * 1.03+"px"
    select.css("width", $("#template")[0].offsetWidth*1.03+"px");
}

$(".tooltip").hover(
    function() {
        var tooltipText = $(this).find(".tooltiptext");
        var left = $(this).offset().left + $(this).outerWidth()/2 - tooltipText.outerWidth()/2;
        var top = $(this).offset().top - tooltipText.outerHeight() - 5;
        tooltipText.css({left: left, top: top});
    }, function() {
        return;
    }
);

//$(window).resize(function(){
function setFillHeight() {
    $(".fill").each(function(index) {
        $(this).css({height: $(window).height() - $("#template").outerHeight() - $(this).offset().top - 10});
    });
}

$(document).ready(function() {
    // force a load of the initial workspace
    $("#workspace").trigger("change");
    $("#nav").css("visibility", "visible");
});
