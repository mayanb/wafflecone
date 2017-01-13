function attributeMouseIn(e) {
	$(this).addClass("highlighted")
	$(this).find(".delete-attribute").removeClass("hidden2")
} 

function attributeMouseOut (e) {
	$(this).removeClass("highlighted")
	$(this).find(".delete-attribute").addClass("hidden2")
}

function reloadAttributesView() {

	$("#attribute-list").empty()

	for (var i = 0; i < attributes.length; i++) {
		var attribute = attributes[i]

		var jq = $(".attribute-list-item.template").clone(true, true).appendTo($('#attribute-list'))
			.hover(attributeMouseIn, attributeMouseOut).removeClass("template")
			.data(attribute)
			.attr("id", "attribute" + i)

		jq.find(".is-upgraded").removeClass("is-upgraded").removeAttr("data-upgraded")

		jq.find("form").attr("name", "attribute" + i)

		jq.find(".attribute-title").val(attribute.name).attr("id", "attribute-input" + i).data({val : attribute.name, parent_id})
		jq.find("label").attr("for", "attribute" + i)

		jq.find(".delete-attribute").attr("for", "attr" + i)
		jq.find("button").attr("for", "attribute" + i)
	}

	componentHandler.upgradeDom()
}

function reloadProcessView() {
	for (var i = 0; i < processes.length; i++) {
		var process = processes[i]
		var jq = $(".process-list-item.template").clone(true, true).appendTo($('#process-list'))
			.removeClass("template")
			.attr("id", "process-list-" + process.id)
			.data(process)

		jq.find(".process-title").html(process.name).addClass("field-text").addClass("name-" + process.id)
	}

}

function refreshProcess(data) {
	var p = $("#process-list-" + data.id)
	p.data(data)
	p.html(data.name)
}

function reloadForm(process) {
	$(".processForm").data(process.data())

	updateMomos($(".processForm .momo"), process.data())

	getAttributes(process.data().id, function (data) {
		for (var i = 0; i < data.length; i++) {
			var momo = makeMomo("attribute", data[i], "name", false, true)
			momo.data()["save"] = saveAttribute
			$("#attribute-list").append(momo)
		}

	}, function () {})
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

		reloadForm(process)
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

function showAreYouSureDialog(title, text, continueFunction, cancelFunction) {
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
        		onClick: cancelFunction
    		},
    		cancelable: false,
    		contentStyle: {'max-width': '500px'}
		})
}

