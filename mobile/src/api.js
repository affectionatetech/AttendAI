import * as Crypto from "expo-crypto";
import * as SecureStore from "expo-secure-store";
import { Platform } from "react-native";

const API_URL =
  process.env.EXPO_PUBLIC_API_URL ||
  (Platform.OS === "web"
    ? "http://127.0.0.1:8000/api/v1"
    : "http://10.0.2.2:8000/api/v1");

async function getStored(key) {
  return Platform.OS === "web"
    ? globalThis.localStorage?.getItem(key) || null
    : SecureStore.getItemAsync(key);
}

async function setStored(key, value) {
  if (Platform.OS === "web") {
    globalThis.localStorage?.setItem(key, value);
  } else {
    await SecureStore.setItemAsync(key, value);
  }
}

async function removeStored(key) {
  if (Platform.OS === "web") {
    globalThis.localStorage?.removeItem(key);
  } else {
    await SecureStore.deleteItemAsync(key);
  }
}

export async function api(path, options = {}) {
  const token = await getStored("attendai_access");

  const response = await fetch(`${API_URL}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(options.headers || {}),
    },
  });

  const data =
    response.status === 204
      ? null
      : await response.json().catch(() => null);

  if (!response.ok) {
    const detail =
      data?.detail ||
      Object.values(data || {}).flat().join(" ") ||
      "Unable to complete the request.";

    throw new Error(detail);
  }

  return data;
}

export async function signIn(email, password) {
  const result = await api("/auth/login/", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });

  if (result.user.role !== "student") {
    throw new Error("This application is for student accounts only.");
  }

  await setStored("attendai_access", result.access);
  await setStored("attendai_refresh", result.refresh);
  await setStored("attendai_user", JSON.stringify(result.user));

  return result.user;
}

export async function restoreUser() {
  const stored = await getStored("attendai_user");
  return stored ? JSON.parse(stored) : null;
}

export async function signOut() {
  await Promise.all(
    ["attendai_access", "attendai_refresh", "attendai_user"].map(
      removeStored
    )
  );
}

export async function deviceIdentifier() {
  let identifier = await getStored("attendai_device");

  if (!identifier) {
    identifier = Crypto.randomUUID();
    await setStored("attendai_device", identifier);
  }

  return identifier;
}