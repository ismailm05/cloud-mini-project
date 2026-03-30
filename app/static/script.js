const taskForm = document.getElementById("task-form");
const taskInput = document.getElementById("task-input");
const taskList = document.getElementById("task-list");
const statusMessage = document.getElementById("status-message");

function setStatus(message, isError = false) {
  statusMessage.textContent = message;
  statusMessage.style.color = isError ? "#b91c1c" : "#475569";
}

function renderTasks(tasks) {
  taskList.innerHTML = "";

  if (!tasks.length) {
    const emptyItem = document.createElement("li");
    emptyItem.className = "empty-state";
    emptyItem.textContent = "No tasks yet.";
    taskList.appendChild(emptyItem);
    return;
  }

  tasks.forEach((task) => {
    const listItem = document.createElement("li");
    listItem.className = "task-item";

    const title = document.createElement("span");
    title.className = "task-title";
    title.textContent = task.title;

    const deleteButton = document.createElement("button");
    deleteButton.className = "delete-button";
    deleteButton.textContent = "Delete";
    deleteButton.addEventListener("click", () => deleteTask(task.id));

    listItem.appendChild(title);
    listItem.appendChild(deleteButton);
    taskList.appendChild(listItem);
  });
}

async function loadTasks() {
  setStatus("Loading tasks...");

  try {
    const response = await fetch("/tasks");
    if (!response.ok) {
      throw new Error("Failed to load tasks");
    }

    const data = await response.json();
    renderTasks(data.tasks || []);
    setStatus("");
  } catch (error) {
    setStatus(error.message, true);
  }
}

async function addTask(title) {
  setStatus("Adding task...");

  try {
    const response = await fetch("/tasks", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ title }),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.error || "Failed to add task");
    }

    taskInput.value = "";
    await loadTasks();
    setStatus("Task added.");
  } catch (error) {
    setStatus(error.message, true);
  }
}

async function deleteTask(taskId) {
  setStatus("Deleting task...");

  try {
    const response = await fetch(`/tasks/${taskId}`, {
      method: "DELETE",
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.error || "Failed to delete task");
    }

    await loadTasks();
    setStatus("Task deleted.");
  } catch (error) {
    setStatus(error.message, true);
  }
}

taskForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const title = taskInput.value.trim();

  if (!title) {
    setStatus("Please enter a task title.", true);
    return;
  }

  await addTask(title);
});

loadTasks();
