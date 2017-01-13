var addAttribute = function () {
	var processID = $(".processForm").data().id

	var momo = makeMomo("attribute", {"process_type" : processID, "name" : ""}, "name", false, true)

	momo.addClass("new-momo")

	// custom cancel/delete button
	momo.find("input").off("blur").blur(function (e) {
		var input = $(this)

		  setTimeout(function () { 

		    if (saving) 
		      return

		    var momo = $(".new-momo")
		    momo.remove()
		  }, 200)
	})

	momo.find(".cancel").off("click").click(function (e) { e.preventDefault() }).find("i").text("cancel")

	momo.find(".done").off("click").click(function (e) {
		e.preventDefault()
		var saving = true

		var momoID = $(this).attr("data-for")
		var momo = $("#" + momoID)
		momo.find('input').attr("disabled", true)

		var newData = jQuery.extend(true, {}, momo.data().data)
		newData[momo.data().field] = momo.find('input').val()

		console.log(newData)

		createAttribute(newData, function (data) {
			momo.remove()
			var newMomo = makeMomo("attribute", data, "name", false, true)
			$("#attribute-list").prepend(newMomo)
			var saving = false
		}, function () {
			momo.find(".cancel").click()
		})
	})

	$("#attribute-list").prepend(momo)

	componentHandler.upgradeDom()

	momo.find("input").focus()
}

function addProcess() {
	var d = {id: -1}
	$(".processForm").hide()
	$(".new-process-form").show()

	reloadForm(d, ".new-process-form")
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

function refreshProcess(data, form) {
	var p = $("#process-list-" + data.id)
	p.data(data)
	p.html(data.name)
}

function reloadForm(data, form) {

	if (!data.id || data.id < 0) {
		$(".new-process-actions").show()
	} else {
		$(".new-process-actions").hide()
	}

	$(form).data(data)

	updateMomos($(form + " .momo"), data)

	getAttributes(data.id, function (data) {
		for (var i = 0; i < data.length; i++) {
			var momo = makeMomo("attribute", data[i], "name", false, true)
			momo.data()["save"] = saveAttribute
			momo.data()["remove"] = deleteAttribute
			$("#attribute-list").append(momo)
		}

	}, function () {})
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

		reloadForm(process.data(), ".processForm")
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

