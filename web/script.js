async function getUserMedia() {
  if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
    return await navigator.mediaDevices.getUserMedia({
      video: true
    })
  } else {
    alert("getUserMedia not supported on your browser!");
  }
}

const threshold = 0.6;
const classesDir = {
  1: {
    name: 'Suzanne',
    id: 1,
  },
}

async function predict(model, img, canvas) {
  tf.engine().startScope()
  // ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
  const tfImg = tf.browser.fromPixels(img).toInt();
  const expandedImg = tfImg.transpose([0, 1, 2]).expandDims();
  const predictions = await model.executeAsync(expandedImg);


  for (let i = 0; i < 8; i++) {
    console.log(predictions[i].arraySync());
    console.log(predictions[i])
  }
  const boxes = predictions[6].arraySync(); // shape [0, 100, 4]
  const scores = predictions[1].arraySync(); // shape [1, 100]
  const classes = predictions[7].dataSync(); // shape [1, 100]
  const detectionObjects = []

  scores[0].forEach((score, i) => {
    if (score > threshold) {
      const bbox = [];
      const minY = boxes[0][i][0] * img.height;
      const minX = boxes[0][i][1] * img.width;
      const maxY = boxes[0][i][2] * img.height;
      const maxX = boxes[0][i][3] * img.width;
      bbox[0] = minX;
      bbox[1] = minY;
      bbox[2] = maxX - minX;
      bbox[3] = maxY - minY;
      const c = classesDir[classes[i]]
      detectionObjects.push({
        class: classes[i],
        label: c ? c.name : 'Unknown',
        score: score.toFixed(4),
        bbox: bbox
      })
    }
  })
  tf.engine().endScope()
  return detectionObjects
}

;(async () => {
  const model = await tf.loadGraphModel("/model/model.json");
  const stream = await getUserMedia()
  if (!stream) {
    throw new Error("media stream not available")
  }
  const cameraVideo = document.createElement("video");
  cameraVideo.srcObject = stream;
  cameraVideo.play();
  await (new Promise((resolve, reject) => {
    cameraVideo.addEventListener("playing", () => {
      resolve(0)
    })
  }))

  const mainCanvas = document.createElement("canvas");
  mainCanvas.width = cameraVideo.videoWidth
  mainCanvas.height = cameraVideo.videoHeight
  const tmpCanvas = document.createElement("canvas");
  tmpCanvas.width = cameraVideo.videoWidth
  tmpCanvas.height = cameraVideo.videoHeight
  const tmpCtx = tmpCanvas.getContext("2d");

  /*
  const inputElem = document.createElement("input")
  inputElem.type = "file"
  inputElem.accept = "image/*"
  inputElem.addEventListener("change", (e) => {
    const  files = e.target.files;
    const reader = new FileReader();
    reader.onload = (ee) => {
      const img = new Image()
      img.src = ee.target.result
      img.onload = () => {
        predict(img)
      }
    }
    reader.readAsDataURL(files[0]);
  })
  document.body.appendChild(inputElem)
  */
  const measurementElem = document.createElement("div")

  document.body.appendChild(mainCanvas)
  document.body.appendChild(measurementElem)

  async function loop() {
    const startTime = performance.now()
    tmpCtx.drawImage(cameraVideo, 0, 0, tmpCanvas.width, tmpCanvas.height);
    const objects = await predict(model, tmpCanvas, mainCanvas)
    const ctx = mainCanvas.getContext("2d");
    ctx.drawImage(tmpCanvas, 0, 0, mainCanvas.width, mainCanvas.height);
    objects.forEach(item => {
      const x = item['bbox'][0];
      const y = item['bbox'][1];
      const width = item['bbox'][2];
      const height = item['bbox'][3];

      // Draw the bounding box.
      ctx.strokeStyle = "#00FFFF";
      ctx.lineWidth = 4;
      ctx.strokeRect(x, y, width, height);

      // Draw the label background.
      ctx.fillStyle = "#00FFFF";
      const scoreText = item["label"] + " " + (100 * item["score"]).toFixed(2) + "%";
      const textWidth = ctx.measureText(scoreText).width;
      const textHeight = 16
      ctx.fillRect(x, y, textWidth, textHeight * 1.5);
      ctx.fillStyle = "#000000";
      ctx.fillText(scoreText, x, y + textHeight / 2);
    });
    const dt = performance.now() - startTime;
    measurementElem.innerText = `${dt.toFixed(2)} ms`
    requestAnimationFrame(loop);
  }
  requestAnimationFrame(loop)
})();