let quizData;
let index = 0;
let correct_qs = 0;

function shuffleQuestions(data) {
  let array = data.questions;
  let currentIndex = array.length,
    randomIndex;

  while (currentIndex != 0) {
    randomIndex = Math.floor(Math.random() * currentIndex);
    currentIndex--;

    [array[currentIndex], array[randomIndex]] = [
      array[randomIndex],
      array[currentIndex],
    ];
  }

  return { ...data, questions: array };
}

async function getQuizData() {
  return fetch("/api/data", {
    method: "GET",
  })
    .then((response) => response.json())
    .then((json) => {
      quizData = shuffleQuestions(json);
    });
}

function displayQuestions(number, data) {
  document.getElementById("question-num").innerHTML = `${number}/150`;
  document.getElementById("question").innerHTML = data["text"];

  document.getElementById("ans-a-label").innerHTML = data["answers"][0];
  document.getElementById("ans-b-label").innerHTML = data["answers"][1];
  document.getElementById("ans-c-label").innerHTML = data["answers"][2];
  document.getElementById("ans-d-label").innerHTML = data["answers"][3];
}

function validateAnswer() {
  let selected_answer_letter = document.querySelector(
    "input[name=answer_rb]:checked"
  ).value;
  let answer = document.getElementById(
    `ans-${selected_answer_letter}-label`
  ).innerText;
  let data = quizData["questions"][index];

  if (data["answers"][data["corr"]] === answer) {
    Swal.fire({
      title: "Tačan odgovor!",
      icon: "success",
      confirmButtonText: "Nastavi dalje",
    }).then((_) => {
      index++;
      ++correct_qs;

      document.getElementById("answers-correct").innerHTML = correct_qs;
      defaultBehaviourDQ();
    });
  } else {
    Swal.fire({
      title: "Netačan odgovor!",
      html: `Vi ste izabrali odgovor, <br><b>${answer}</b>. <br>a tačan je,<br><b>${
        data["answers"][data["corr"]]
      }</b>`,
      icon: "error",
      confirmButtonText: "Nastavi dalje",
    }).then((_) => {
      document.getElementById("answers-incorrect").innerText =
        index - correct_qs;
      index++;
      defaultBehaviourDQ();
    });
  }
}

function defaultBehaviourDQ() {
  displayQuestions(index.toString(), quizData["questions"][index]);
}

window.onload = async function () {
  await getQuizData();

  document
    .querySelector(".validate-btn")
    .addEventListener("click", () => validateAnswer());
  document.getElementById(
    "id-key"
  ).innerHTML = `<strong">${quizData["id"]}</strong> tvoj identifikacijski kod`;

  defaultBehaviourDQ();
};
