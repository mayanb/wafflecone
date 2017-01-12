function reloadAttributesView() {

	$("#attribute-list").empty()

	for (var i = 0; i < attributes.length; i++) {
		var attribute = attributes[i]
		var jq = $(".attribute-list-item.template").clone(true, true).appendTo($('#attribute-list'))
			.removeClass("template")

		jq.find(".attribute-title").text(attribute.name)
		jq.find(".delete-attribute").attr("for", i)
	}
}

function removeAttributeView(i) {
	var childNum = parseInt(i) + 1
	$(".attribute-list-item:nth-child(" + childNum + ")").remove()
}

function reloadProcessView() {
	for (var i = 0; i < processes.length; i++) {
		var process = processes[i]
		var jq = $(".process-list-item.template").clone(true, true).appendTo($('#process-list'))
			.removeClass("template")
			.attr("id", i)

		jq.find(".process-title").html(process.name).addClass("field-text").addClass("name-" + process.id)
	}

}

function reloadForm() {
	var form = $("form")
	var json = processes[selectedProcess]

	$(".is-active").removeClass("is-active")
	$("input").attr("disabled", false)

	getAttributes(json.id, reloadAttributesView, function () {
		// show error
	})

	for (var prop in json) {
		form.find("#" + prop).val(json[prop]).parent().addClass("is-dirty")
	}
}

function updateAll(json) {
	var id = json.id
	var body = $("body")

	for (var field in json) {
		body.find(".field-text." + field + "-" + id).text(json[field])
	}
}

function showError(title, text) {
	showDialog({
    		id: 'dialog-id',
    		title: title,
    		text: text,
    		neutral: {
        		id: 'ok-button',
        		title: 'OK',
        		onClick: function() {  }
    		},
    		cancelable: true,
    		contentStyle: {'max-width': '500px'}
		})
}

function clickOnProcess(process) {

		$(".process-list-item").removeClass("mdl-color--deep-purple-500").addClass("mdl-color--white")

		process.addClass("mdl-color--deep-purple-500").removeClass("mdl-color--white")

		reloadForm()
}

function showContinueDialog(continueFunction) {

	if (!saving) {
		continueFunction()
		return
	}

	showDialog({
    		id: 'dialog-id',
    		title: "Are you sure you want to leave this page?",
    		text: "Your changes might not be saved.",
    		negative: {
        		id: 'continue-button',
        		title: "Yes, I'm sure",
        		onClick: continueFunction
    		},
    		positive: {
    			id: 'cancel-button',
        		title: 'Go back',
        		onClick: function () {}
    		},
    		cancelable: true,
    		contentStyle: {'max-width': '500px'}
		})
}

function showAreYouSureDialog(title, text, continueFunction) {
	showDialog({
    		id: 'dialog-id',
    		title: title,
    		text: text,
    		negative: {
        		id: 'continue-button',
        		title: "Yes, I'm sure",
        		onClick: continueFunction
    		},
    		positive: {
    			id: 'cancel-button',
        		title: 'Go back',
        		onClick: function () {}
    		},
    		cancelable: true,
    		contentStyle: {'max-width': '500px'}
		})
}

