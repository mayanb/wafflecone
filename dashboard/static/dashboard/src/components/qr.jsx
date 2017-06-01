function mountQR() {
  if(dymo.label.framework.init)
    dymo.label.framework.init(init)
  else
  init()
}

/* function : init
 * ---------------
 * This function is called after the Dymo Framework inits and sets up the webpage.
 */

function init() {
}

function print(numLabels, text, success, always) {
  $.ajax({
      url: "codes/",
      data: {count : numLabels},
    })
  .done(function (data) {
    success(data)
  })
  .always(function () {
    always()
  })
}

var errorCallback = function(errorMessage) {
  alert("Error: " + errorMessage);  
}

function short(str) {
  if (!str)
    return ""
  var codes = str.split('-')
  if (codes.length > 2) {
    codes.splice(1, 1)
  }
  return codes.join('-')
}

function getCode(str) {
  var codes = str.split('-')
  if (codes[1])
    return codes[1]
  return str
}

function calibrate() {
  BrowserPrint.getDefaultDevice("printer", function (device) {
    device.send('! U1 setvar "media.type" "label"\n! U1 setvar "media.sense_mode" "bar"\n~jc^xa^jus^xz', undefined, errorCallback)
  })
}

function printQRs_zebra(uuids, task, notes) {
  try {
    var zpl = ""
    uuids.map(function (uuid) {
      zpl += `
        ^XA
        ^FO30,36
          ^BQ,2,6^FDMA,${uuid}
        ^FS
        ^FO70,260
          ^AE,10
          ^FD${uuid.substring(uuid.length-6)}
        ^FS
        ^FO270,70
          ^A0,180
          ^FD${getCode(task.data.display)}
        ^FS
        ^FO30,300
          ^GB${609-72},1,3
        ^FS
        ^FO30,330
          ^A0,60
          ^FD${task.data.display}
        ^FS
        ^XZ`
    })

    BrowserPrint.getDefaultDevice("printer", function(device) {
      device.send(zpl, undefined, errorCallback);
    })
  } catch (e) {
    alert(e.message || e)
  }
}

function printQRs_dymo(uuids, task, notes, qrcode) {
  try {

    // get a printer 
    let printer = getPrinter()

    // clear the current qr code
    qrcode.clear()

    // get the label printing xml
    var label = dymo.label.framework.openLabelXml(getXML())
    var labelSetBuilder = new dymo.label.framework.LabelSetBuilder()

    // convert the svg to an image url
    var DOMURL = self.URL || self.webkitURL || self;
    var svgString = new XMLSerializer().serializeToString(document.querySelector('svg'));
    var svg = new Blob([svgString], {type: "image/svg+xml;charset=utf-8"});
    var url = DOMURL.createObjectURL(svg);

    // create an image and set the URL to the svg image. Then when it's loaded,
    // convert the svg to canvas, and then attach it to the label record
    // And then attach the qr code.
    var img = new Image();
    img.onload = function() {
      var canvas = document.getElementById('canvastest').querySelector('canvas')
      var ctx = canvas.getContext('2d');

      uuids.map(function (uuid) {
        createBackingImage(ctx, img, uuid)
        let backingImage = canvas.toDataURL().substr('data:image/png;base64,'.length)
        let qrImage = getQRimage(qrcode, uuid)
        let record = labelSetBuilder.addRecord()
        record.setText('qrImage', qrImage)
        record.setText('backingImage', backingImage)
      })

      // print the qr code
      label.print(printer, "", labelSetBuilder)
      qrcode.clear()
    }

    img.src = url;
  }  catch(e) {
    alert(e.message || e)
  }
}

// the backing image is all the text
function createBackingImage(ctx, svg, uuid) {
  // clear canvas
  ctx.fillStyle = '#fff';
  ctx.fillRect(0, 0, 431, 241);

  // add backing image + qr text
  ctx.fillStyle = '#000'
  ctx.font = "20px Overpass Mono";
  ctx.drawImage(svg, 0, 0);
  ctx.font = "20px Overpass Mono";
  ctx.fillText(uuid.substr(uuid.length-6), 71, 216)
}

function getQRimage(qrcode, uuid) {
  qrcode.clear()
  qrcode.makeCode(uuid)
  let url = document.getElementById('qrtest').querySelector('canvas').toDataURL()
  let pngBase64 = url.substr('data:image/png;base64,'.length);
  return pngBase64
}

/* function : getPrinter
 * ---------------
 * Gets a DYMO printer. TODO: Maybe update this to use CUPS API?
 */
function getPrinter() {
  // select printer to print on
  // for simplicity sake just use the first LabelWriter printer
  var printers = dymo.label.framework.getPrinters();
  console.log(printers)
  if (!printers || printers.length == 0)
    throw "No DYMO printers are installed. Install DYMO printers."

  var i = -1;
  for (var j = 0; j < printers.length; ++j) {
    var printer = printers[j];
    if (printer.printerType == "LabelWriterPrinter" && printer.isConnected) {
      i = j
      break;
    }
  }

  if (i == -1) 
    throw "No DYMO printers are connected."

  return printers[i].name

}

/* function : getXML
 * -----------------
 * Returns XML format of a label. TODO: Change this to AJAX get.
 */
function getXML() {
  var labelXml = `<?xml version="1.0" encoding="utf-8"?>
<DieCutLabel Version="8.0" Units="twips">
  <PaperOrientation>Landscape</PaperOrientation>
  <Id>Shipping</Id>
  <PaperName>30323 Shipping</PaperName>
  <DrawCommands>
    <RoundRectangle X="0" Y="0" Width="3060" Height="5715" Rx="270" Ry="270"/>
  </DrawCommands>
  <ObjectInfo>
    <ImageObject>
      <Name>backingImage</Name>
      <ForeColor Alpha="255" Red="0" Green="0" Blue="0"/>
      <BackColor Alpha="0" Red="255" Green="255" Blue="255"/>
      <LinkedObjectName></LinkedObjectName>
      <Rotation>Rotation0</Rotation>
      <IsMirrored>False</IsMirrored>
      <IsVariable>False</IsVariable>
      <Image></Image>
      <ScaleMode>Fill</ScaleMode>
      <BorderWidth>0</BorderWidth>
      <BorderColor Alpha="255" Red="0" Green="0" Blue="0"/>
      <HorizontalAlignment>Center</HorizontalAlignment>
      <VerticalAlignment>Center</VerticalAlignment>
    </ImageObject>
    <Bounds X="196" Y="0" Width="5323.2" Height="2918.4"/>
  </ObjectInfo>
  <ObjectInfo>
    <ImageObject>
      <Name>qrImage</Name>
      <ForeColor Alpha="255" Red="0" Green="0" Blue="0"/>
      <BackColor Alpha="0" Red="255" Green="255" Blue="255"/>
      <LinkedObjectName></LinkedObjectName>
      <Rotation>Rotation0</Rotation>
      <IsMirrored>False</IsMirrored>
      <IsVariable>False</IsVariable>
      <Image></Image>
      <ScaleMode>Uniform</ScaleMode>
      <BorderWidth>0</BorderWidth>
      <BorderColor Alpha="255" Red="0" Green="0" Blue="0"/>
      <HorizontalAlignment>Center</HorizontalAlignment>
      <VerticalAlignment>Center</VerticalAlignment>
    </ImageObject>
    <Bounds X="430.5774" Y="360.9652" Width="1640.358" Height="1488.177"/>
  </ObjectInfo>
</DieCutLabel>
`
  return labelXml;
}

export {mountQR, printQRs_dymo, printQRs_zebra, calibrate}