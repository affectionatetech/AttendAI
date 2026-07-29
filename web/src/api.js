const API_URL = "http://127.0.0.1:8000/api/v1";

export function getToken() {
  return localStorage.getItem("attendai_access");
}

export async function api(path, options = {}) {
  const headers = { ...(options.headers || {}) };
  if (!(options.body instanceof FormData)) headers["Content-Type"] = "application/json";
  if (getToken()) headers.Authorization = `Bearer ${getToken()}`;
  const response = await fetch(`${API_URL}${path}`, { ...options, headers });
  if (response.status === 401) {
    localStorage.removeItem("attendai_access");
    localStorage.removeItem("attendai_user");
  }
  const data = response.status === 204 ? null : await response.json().catch(() => null);
  if (!response.ok) {
    const message = data?.detail || Object.values(data || {}).flat().join(" ") || "The request could not be completed.";
    throw new Error(message);
  }
  return data;
}

export async function login(email, password) {
  const result = await api("/auth/login/", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
  localStorage.setItem("attendai_access", result.access);
  localStorage.setItem("attendai_user", JSON.stringify(result.user));
  return result.user;
}

export function logout() {
  localStorage.removeItem("attendai_access");
  localStorage.removeItem("attendai_user");
}

export async function downloadReport() {
  const response = await fetch(`${API_URL}/attendance/reports/attendance.csv`, {
    headers: { Authorization: `Bearer ${getToken()}` },
  });
  if (!response.ok) throw new Error("The report could not be downloaded.");
  const url = URL.createObjectURL(await response.blob());
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = "attendance-report.csv";
  anchor.click();
  URL.revokeObjectURL(url);
}
