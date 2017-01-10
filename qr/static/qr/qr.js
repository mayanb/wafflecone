$(document).ready(function () {
  if(dymo.label.framework.init)
    dymo.label.framework.init(init)
  else
  init()
})

function init() {
  var printButton = $("#printButton")

  printButton.click(function (e) {
    e.preventDefault()

    $(".preview").remove()

    var numLabels = $("#numLabels").val()

    if ($.isNumeric(numLabels)) {
      numLabels = parseInt(numLabels)
    } else {
      console.log("please enter a valid number!")
      return
    }

    $.ajax({
      url: "codes/",
      data: {count : numLabels},
      success: success
    })

  })

  $("#resetButton").click(function (e) {
    e.preventDefault()
    reset()
  })
}

function reset() {
  $("input").val("")
  $(".preview").remove()

}

function success(data) {

  var uuids = data.split(/\s+/)

    try {
      var displayText = $("#displayText").val()

      // get label xml
      var label = dymo.label.framework.openLabelXml(getXML())
      var labelSetBuilder = new dymo.label.framework.LabelSetBuilder()

      var defs = []
      for (var i = 0; i < uuids.length; i++) {
        defs.push(getLabelRecord(labelSetBuilder, displayText, uuids[i]))
      }

      $.when.apply(null, defs).done(function() {
        label.print(getPrinter(), "", labelSetBuilder);
      })

    } catch(e) {
      alert(e.message || e);
    }

}

function preview(labelSet) {
  var labels = labelSet.getRecords(); //get all the records we add to build the labelSet.

  for (var i = 0; i< labels.length; i++) {
    var label = dymo.label.framework.openLabelXml(getXML())

    label.setObjectText("displayText1", labels[i]["displayText1"])
    label.setObjectText("displayText2", labels[i]["displayText2"])
    label.setObjectText("qrText", labels[i]["qrText"])
    label.setObjectText("qrImage", labels[i]["qrImage"])

    pngData = label.render();
    var labelImage = $("body").append(
      $("<img/>").addClass("preview")
      .attr("src","data:image/png;base64," + pngData)
    )
  }
}

function getLabelRecord(labelSetBuilder, displayText, code) {
  var deferred = $.Deferred();
  var record = labelSetBuilder.addRecord()

  var len = displayText.length
  var dt1 = displayText.substring(0, len-4)
  var dt2 = displayText.substring(len-4, len)

  record.setText("displayText1", dt1)
  record.setText("displayText2", dt2)
  record.setText("qrText", code.substring(43, 43+6))

  var url = 'https://chart.googleapis.com/chart?chs=300x300&cht=qr&choe=UTF-8&chl=' + code
  var img = new Image();
  img.crossOrigin = 'anonymous';
  img.onload = function() {
    try {
      var canvas = document.createElement('canvas')
      canvas.width = 300
      canvas.height = 300
      var context = canvas.getContext('2d');
      context.drawImage(img, 0, 0);

      var dataUrl = canvas.toDataURL('image/png');
      var pngBase64 = dataUrl.substr('data:image/png;base64,'.length);

      record.setText('qrImage', pngBase64);
      deferred.resolve()

    }
    catch(e) {
        alert(e.message || e);
    }
  };
  img.onerror = function() { alert('Unable to load qr-code image') }
  img.src = url

  return deferred.promise()
}

function getPrinter() {
  // select printer to print on
  // for simplicity sake just use the first LabelWriter printer
  var printers = dymo.label.framework.getPrinters();
  if (printers.length == 0)
    throw "No DYMO printers are installed. Install DYMO printers.";

  var printerName = "";
  for (var i = 0; i < printers.length; ++i) {
    var printer = printers[i];
    if (printer.printerType == "LabelWriterPrinter") {
      printerName = printer.name;
      break;
    }
  }

  return printerName

}

function getXML() {
  var labelXml = '<?xml version="1.0" encoding="utf-8"?><DieCutLabel Version="8.0" Units="twips">  <PaperOrientation>Landscape</PaperOrientation>  <Id>Shipping</Id>  <PaperName>30323 Shipping</PaperName>  <DrawCommands>    <RoundRectangle X="0" Y="0" Width="3060" Height="5715" Rx="270" Ry="270"/>  </DrawCommands>  <ObjectInfo>    <ImageObject>      <Name>qrImage</Name>      <ForeColor Alpha="255" Red="0" Green="0" Blue="0"/>      <BackColor Alpha="0" Red="255" Green="255" Blue="255"/>      <LinkedObjectName></LinkedObjectName>      <Rotation>Rotation0</Rotation>      <IsMirrored>False</IsMirrored>      <IsVariable>False</IsVariable>      <Image></Image>      <ScaleMode>Fill</ScaleMode>      <BorderWidth>0</BorderWidth>      <BorderColor Alpha="255" Red="0" Green="0" Blue="0"/>      <HorizontalAlignment>Center</HorizontalAlignment>      <VerticalAlignment>Center</VerticalAlignment>    </ImageObject>    <Bounds X="491.4844" Y="286.4062" Width="2160" Height="2160"/>  </ObjectInfo>  <ObjectInfo>    <TextObject>      <Name>displayText1</Name>      <ForeColor Alpha="255" Red="0" Green="0" Blue="0"/>      <BackColor Alpha="0" Red="255" Green="255" Blue="255"/>      <LinkedObjectName></LinkedObjectName>      <Rotation>Rotation0</Rotation>      <IsMirrored>False</IsMirrored>      <IsVariable>False</IsVariable>      <HorizontalAlignment>Center</HorizontalAlignment>      <VerticalAlignment>Middle</VerticalAlignment>      <TextFitMode>ShrinkToFit</TextFitMode>      <UseFullFontHeight>True</UseFullFontHeight>      <Verticalized>False</Verticalized>      <StyledText>        <Element>          <String>CVB-R</String>          <Attributes>            <Font Family="OPTINational-Gothic" Size="72" Bold="False" Italic="False" Underline="False" Strikeout="False"/>            <ForeColor Alpha="255" Red="0" Green="0" Blue="0"/>          </Attributes>        </Element>      </StyledText>    </TextObject>    <Bounds X="2834.141" Y="518.2031" Width="2374.062" Height="921.25"/>  </ObjectInfo>  <ObjectInfo>    <TextObject>      <Name>displayText2</Name>      <ForeColor Alpha="255" Red="0" Green="0" Blue="0"/>      <BackColor Alpha="0" Red="255" Green="255" Blue="255"/>      <LinkedObjectName></LinkedObjectName>      <Rotation>Rotation0</Rotation>      <IsMirrored>False</IsMirrored>      <IsVariable>False</IsVariable>      <HorizontalAlignment>Center</HorizontalAlignment>      <VerticalAlignment>Middle</VerticalAlignment>      <TextFitMode>ShrinkToFit</TextFitMode>      <UseFullFontHeight>True</UseFullFontHeight>      <Verticalized>False</Verticalized>      <StyledText>        <Element>          <String>1010</String>          <Attributes>            <Font Family="OPTINational-Gothic" Size="72" Bold="False" Italic="False" Underline="False" Strikeout="False"/>            <ForeColor Alpha="255" Red="0" Green="0" Blue="0"/>          </Attributes>        </Element>      </StyledText>    </TextObject>    <Bounds X="2831.484" Y="1447.266" Width="2379.375" Height="1217.5"/>  </ObjectInfo>  <ObjectInfo>    <TextObject>      <Name>qrText</Name>      <ForeColor Alpha="255" Red="0" Green="0" Blue="0"/>      <BackColor Alpha="0" Red="255" Green="255" Blue="255"/>      <LinkedObjectName></LinkedObjectName>      <Rotation>Rotation0</Rotation>      <IsMirrored>False</IsMirrored>      <IsVariable>False</IsVariable>      <HorizontalAlignment>Center</HorizontalAlignment>      <VerticalAlignment>Middle</VerticalAlignment>      <TextFitMode>ShrinkToFit</TextFitMode>      <UseFullFontHeight>True</UseFullFontHeight>      <Verticalized>False</Verticalized>      <StyledText>        <Element>          <String>qrcode1</String>          <Attributes>            <Font Family="Source Code Pro" Size="13" Bold="False" Italic="False" Underline="False" Strikeout="False"/>            <ForeColor Alpha="255" Red="0" Green="0" Blue="0"/>          </Attributes>        </Element>      </StyledText>    </TextObject>    <Bounds X="631.0938" Y="2370.078" Width="1880.781" Height="600"/>  </ObjectInfo></DieCutLabel>'
  return labelXml;
}
