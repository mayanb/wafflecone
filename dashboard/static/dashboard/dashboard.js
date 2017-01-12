var separator = $('<div class="demo-separator mdl-cell--1-col"></div>')

var processes = []
var currentAttributes = []
var attributesLoaded = false
var selectedProcess = -1

var saving = false

$(document).ready(function () {

	setup()

	getProcesses(function () {
		reloadProcessView()
		$(".process-list-item").eq(0).click()
	}, function () {})

	$(".process-list-item").click(function (e) {
		e.preventDefault()

		// if you selected the same thing again then dont do anything
		var select = parseInt($(this).attr("id"))
		if (selectedProcess == select) 
			return

		var p = $(this)

		showContinueDialog(function () {
			saving = false
			selectedProcess = select
			clickOnProcess(p)
		})
	})


	$(".attribute-list-item").hover(function (e) {
		$(this).addClass("highlighted")
		$(this).find(".delete-attribute").removeClass("hidden2")
	}, function (e) {
		$(this).removeClass("highlighted")
		$(this).find(".delete-attribute").addClass("hidden2")
	})

	$("input").focus(function (e) {
		var id = $(this).attr("id")
		$("form[name=" + id + "]").find("button").removeClass("hidden2")
	}).blur(function (e) {
		var id = $(this).attr("id")
		var val = processes[selectedProcess][id]
		$("#" + id).val(val)
		
		if (!val || val.trim() == "") {
			$(this).parent().removeClass("is-dirty")
		} else {
			$(this).parent().addClass("is-dirty")
		}

		$("form[name=" + id + "]").find("button").addClass("hidden2")
	})

	$("form button.done").mousedown(function (e) {
		var id = $(this).attr("for")
		$("#" + id).prop("disabled", true)
		$("form[name=" + id + "] .mdl-spinner").addClass("is-active")
		saveProcess(function () {
			reloadForm()
			updateAll(processes[selectedProcess])
		}, function () {
			reloadForm()
		})
	})

	$(".delete-attribute").click(function (e) {
		var i = $(this).attr("for")
		deleteAttribute(i, function () {
			console.log("hey")
			removeAttributeView(i)
		}, function () {})
	})
})

function deleteAttribute(index, success, failure) {
	var attribute = attributes[index]

	var saving = true

	$.ajax("../ics/attributes/" + attribute.id + "/", {
		method: "DELETE"
	}).done(function (data) {
		if (!saving) 
			return
		attributes.splice(index, 1)
		success()
	}).fail(function (data, res, error) {
		if (!saving) 
			return
		showError("Something went wrong", "Looks like something isn't working. Try again later.")
		failure()
	}).always(function () {
		saving = false
	})

}

function saveProcess(success, failure) {
	var newData = collectData()

	saving = true

	$.ajax("../ics/processes/" + processes[selectedProcess].id + "/", {
		method: "PUT",
		data: newData
	}).done(function (data) {
		if (!saving) return
		processes[selectedProcess] = newData
		success()
	}).fail(function (data, res, error) {
		if (!saving) return
		showError("Something went wrong", "Looks like something isn't working. Try again later.")
		failure()
	}).always(function () {
		saving = false
	})
}

function collectData() {
  var newData = jQuery.extend(true, {}, processes[selectedProcess])
  $("form").each(function () {
  	var field = $(this).attr("name")
  	newData[field] = $("#" + field).val()
  })

  return newData
}

function getProcesses(success, failure) {
	processes = []
	$.get("../ics/processes")
		.done(function (data) {
			processes = data
			success()
		})
		.fail(function () {
			showError("Something went wrong", "Looks like something isn't working. Try again later.")
		})
}

function getAttributes(id, success, failure) {
	attributes = []
	attributesLoaded = false
	$.get("../ics/attributes/?process_type=" + id)
		.done(function (data) {
			attributes = data
			attributesLoaded = true
			success()
		})
		.fail(function () {
			attributesLoaded = false
			showError("Something went wrong", "Looks like something isn't working. Try again later.")
		})
}

function upgrade(jq) {
	componentHandler.upgradeElement(jq.eq(0));
}


//---------------------------------------------

function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var cookie = jQuery.trim(cookies[i]);
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

function csrfSafeMethod(method) {
    // these HTTP methods do not require CSRF protection
    return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
}


function setup() {

	var csrftoken = getCookie('csrftoken');

	$.ajaxSetup({
    	beforeSend: function(xhr, settings) {
        	if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
            	xhr.setRequestHeader("X-CSRFToken", csrftoken);
        	}
    	}
	})
}