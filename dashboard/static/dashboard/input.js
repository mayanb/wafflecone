var inputTemplate = ""
var inputTemplateLarge = ""

var inputTemplate = $('<form class="momo" name=""><div class="mdl-textfield mdl-js-textfield"><input class="mdl-textfield__input delegate" type="text"><label class="mdl-textfield__label">Text...</label>  </div>  <button class="mdl-button mdl-js-button mdl-button--icon hidden2 done delegate" for="">    <i class="material-icons">done</i>  </button>  <button class="mdl-button mdl-js-button mdl-button--icon hidden2 cancel delegate" for="">    <i class="material-icons">delete</i>  </button> ')

// momo manages the given field for the data
function makeMomo(prefix, data, field, large, deletable) {
  var momo = $(inputTemplate).clone(true, true)

  if (large)
    momo.find(".mdl-textfield, .mdl-textfield__input, .mdl-textfield__label").addClass("large-textfield  mdl-textfield--floating-label")

  if (!deletable)
    momo.find(".cancel").remove()

  momo.data({
    data: data,
    field: field, 
    prefix: prefix
  })

  resetMomoIDs(momo, prefix, data, field, large, deletable)

  momo.find("input").focus(inputFocused).blur(inputBlurred).val(data[field]).parent().addClass("is-dirty")
  momo.find("label").text(prefix + " " + field)
  momo.find("button").click(doneClicked)

  return momo
}

function resetMomoIDs(momo) {
  var prefix = momo.data().prefix
  var data = momo.data().data
  var field = momo.data().field

  var momoID = ["momo", prefix, data.id, field].join("-")
  var inputID = ["momoInput", prefix, data.id, field].join("-")

  momo.attr("id", momoID)

  momo.find(".delegate").attr("data-for", momoID)
  momo.find("input").attr("id", inputID)
  momo.find("label").attr("for", inputID)
}

function updateMomos(momos, data) {
  momos.each(function (i) {
    var momo = $(this)

    resetMomoIDs(momo)

    var field = momo.data().field
    momo.data().data = data

    momo.find("input").val(data[field]).parent().addClass("is-dirty")
  })
}

function saveMomo(momo, callback, failure) {
  var data = momo.data().data
  var field = momo.data().field

  var newData = jQuery.extend(true, {}, data)
  newData[field] = momo.find("input").val()

  momo.data().save(newData, callback, failure)
}

function initMomos() {
  inputTemplate.hover(mouseIn, mouseOut)
  inputTemplate.find("input").focus(inputFocused).blur(inputBlurred)
}

var inputFocused = function (e) {
  var momoID = $(this).attr("data-for")
  var momo = $("#" + momoID)
  momo.mouseenter()
  momo.find("button").removeClass("hidden2")
}

// we have to set a timeout for some crazy ass reason...
var inputBlurred = function (e) {

  var input = $(this)

  setTimeout(function () { 

    if (saving) 
      return

    var momoID = input.attr("data-for")
    var momo = $("#" + momoID)
    var field = momo.data().field

    var v = momo.data().data[field]
    input.val(v)

    if (!v || v.trim() == "")
      input.parent().removeClass("is-dirty")
    else 
      input.parent().addClass("is-dirty")

    momo.mouseleave()
    momo.find("button").addClass("hidden2")
  }, 200)
}

var doneClicked = function (e) {
  e.preventDefault()

  var momoID = $(this).attr("data-for")
  $("#" + momoID).find("input").attr("disabled", true)

  saveMomo($("#" + momoID), function () {
    saving = false
    $("#" + momoID).find("input").attr("disabled", false)
  }, function () {
    $("#" + momoID).find("input").attr("disabled", false)
    refreshMomos( $("#" + momoID) )
  })
}

var deleteClicked = function (e) {
  e.preventDefault()

  var momoID = $(this).attr("data-for")
  $("#" + momoID).find("input").attr("disabled", true)

  saveMomo($("#" + momoID), function () {
    saving = false
    $("#" + momoID).find("input").attr("disabled", false)
  }, function () {
    $("#" + momoID).find("input").attr("disabled", false)
    refreshMomos( $("#" + momoID) )
  })
}

function refreshMomos(momos) {
  updateMomos(momos, momos.data().data)
}

function mouseIn(e) {

  $(this).addClass("hovering")
  $(this).find(".delete-attribute").removeClass("hidden2")
}

function mouseOut(e) {

  $(this).removeClass("hovering")
  $(this).find(".delete-attribute").addClass("hidden2")
}