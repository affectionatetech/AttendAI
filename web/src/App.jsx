import {
  useCallback,
  useEffect,
  useState,
} from "react";

import {
  AlertTriangle,
  BarChart3,
  BookOpen,
  CalendarDays,
  CheckCircle2,
  ChevronRight,
  ClipboardCheck,
  Download,
  LayoutDashboard,
  LogOut,
  MapPin,
  Menu,
  Plus,
  RefreshCw,
  ShieldCheck,
  UserRoundPlus,
  Users,
  XCircle,
} from "lucide-react";

import {
  api,
  downloadReport,
  getToken,
  login,
  logout,
} from "./api";

const emptySummary = {
  courses: 0,
  sessions: 0,
  attendance_total: 0,
  confirmed: 0,
  rejected: 0,
  pending_review: 0,
  open_fraud_alerts: 0,
};

function Login({ onLogin }) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit(event) {
    event.preventDefault();
    setError("");
    setBusy(true);

    try {
      const user = await login(email, password);

      if (user.role === "student") {
        logout();

        throw new Error(
          "Students use the AttendAI mobile application."
        );
      }

      onLogin(user);
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="login-shell">
      <section className="login-story">
        <div className="brand brand-light">
          <span>
            <ShieldCheck />
          </span>

          AttendAI
        </div>

        <div className="story-copy">
          <p className="eyebrow">
            Attendance intelligence
          </p>

          <h1>
            Verified presence.
            <br />
            Clear decisions.
          </h1>

          <p>
            A privacy-aware attendance platform
            combining bounded location verification,
            explainable risk analysis and human review.
          </p>

          <div className="trust-row">
            <span>
              <MapPin />
              Event-based location
            </span>

            <span>
              <ShieldCheck />
              Human-governed AI
            </span>
          </div>
        </div>

        <p className="copyright">
          AttendAI Institutional Portal
        </p>
      </section>

      <section className="login-panel">
        <form
          className="login-card"
          onSubmit={submit}
        >
          <div className="mobile-brand brand">
            <span>
              <ShieldCheck />
            </span>

            AttendAI
          </div>

          <p className="eyebrow">
            Secure staff access
          </p>

          <h2>Welcome back</h2>

          <p className="muted">
            Sign in to manage attendance and review
            institutional activity.
          </p>

          {error && (
            <div className="notice error">
              <AlertTriangle size={18} />
              {error}
            </div>
          )}

          <label>
            Email address

            <input
              type="email"
              required
              value={email}
              onChange={(event) =>
                setEmail(event.target.value)
              }
              placeholder="name@institution.edu"
            />
          </label>

          <label>
            Password

            <input
              type="password"
              required
              value={password}
              onChange={(event) =>
                setPassword(event.target.value)
              }
              placeholder="Enter your password"
            />
          </label>

          <button
            className="primary full"
            disabled={busy}
          >
            {busy
              ? "Signing in…"
              : "Sign in securely"}

            <ChevronRight size={18} />
          </button>

          <p className="privacy">
            <ShieldCheck size={15} />
            Access is logged and protected by
            role-based permissions.
          </p>
        </form>
      </section>
    </main>
  );
}

const nav = [
  ["dashboard", "Overview", LayoutDashboard],
  ["courses", "Courses", BookOpen],
  ["sessions", "Class sessions", CalendarDays],
  ["enrolments", "Enrolments", Users],
  ["alerts", "Fraud review", ShieldCheck],
  ["reports", "Reports", BarChart3],
];

function Shell({ user, onLogout }) {
  const [page, setPage] = useState("dashboard");
  const [mobileNav, setMobileNav] =
    useState(false);

  function go(value) {
    setPage(value);
    setMobileNav(false);
  }

  return (
    <div className="app-shell">
      <aside
        className={
          mobileNav ? "sidebar open" : "sidebar"
        }
      >
        <div className="brand brand-light">
          <span>
            <ShieldCheck />
          </span>

          AttendAI
        </div>

        <p className="nav-label">Workspace</p>

        <nav>
          {nav.map(([id, label, Icon]) => (
            <button
              key={id}
              className={
                page === id ? "active" : ""
              }
              onClick={() => go(id)}
            >
              <Icon size={19} />
              {label}
            </button>
          ))}
        </nav>

        <div className="side-profile">
          <div className="avatar">
            {user.full_name?.slice(0, 1)}
          </div>

          <div>
            <strong>{user.full_name}</strong>
            <small>{user.role}</small>
          </div>
        </div>

        <button
          className="logout"
          onClick={onLogout}
        >
          <LogOut size={18} />
          Sign out
        </button>
      </aside>

      <div className="workspace">
        <header>
          <button
            className="menu"
            onClick={() =>
              setMobileNav(!mobileNav)
            }
          >
            <Menu />
          </button>

          <div>
            <p className="eyebrow">
              Institutional portal
            </p>

            <h2>
              {
                nav.find(
                  (item) => item[0] === page
                )?.[1]
              }
            </h2>
          </div>

          <div className="role-chip">
            <span />
            {user.role}
          </div>
        </header>

        <main className="content">
          {page === "dashboard" && (
            <Dashboard
              user={user}
              navigate={go}
            />
          )}

          {page === "courses" && (
            <Courses user={user} />
          )}

          {page === "sessions" && <Sessions />}

          {page === "enrolments" && (
            <Enrolments />
          )}

          {page === "alerts" && <Alerts />}

          {page === "reports" && <Reports />}
        </main>
      </div>
    </div>
  );
}

function Loading() {
  return (
    <div className="loading">
      <RefreshCw className="spin" />
      Loading current information…
    </div>
  );
}

function Empty({
  icon: Icon = ClipboardCheck,
  title,
  text,
}) {
  return (
    <div className="empty">
      <span>
        <Icon />
      </span>

      <h3>{title}</h3>
      <p>{text}</p>
    </div>
  );
}

function ErrorBox({ message }) {
  return message ? (
    <div className="notice error">
      <AlertTriangle size={18} />
      {message}
    </div>
  ) : null;
}

function Status({ value }) {
  return (
    <span className={`status ${value}`}>
      {value?.replaceAll("_", " ")}
    </span>
  );
}

function Dashboard({ user, navigate }) {
  const [summary, setSummary] =
    useState(emptySummary);

  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] =
    useState(true);

  const [error, setError] = useState("");

  useEffect(() => {
    Promise.all([
      api("/attendance/dashboard/summary/"),
      api(
        "/attendance/fraud-alerts/?status=open"
      ),
    ])
      .then(([summaryResult, alertResult]) => {
        setSummary(summaryResult);
        setAlerts(alertResult.slice(0, 4));
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return <Loading />;
  }

  const cards = [
    [
      "Total attendance",
      summary.attendance_total,
      ClipboardCheck,
      "navy",
    ],
    [
      "Confirmed",
      summary.confirmed,
      CheckCircle2,
      "green",
    ],
    [
      "Pending review",
      summary.pending_review,
      AlertTriangle,
      "amber",
    ],
    [
      "Rejected",
      summary.rejected,
      XCircle,
      "red",
    ],
  ];

  return (
    <>
      <section className="welcome">
        <div>
          <p className="eyebrow">
            Good to see you
          </p>

          <h1>{user.full_name}</h1>

          <p>
            Here is the latest attendance and
            verification activity.
          </p>
        </div>

        <button
          className="primary"
          onClick={() => navigate("sessions")}
        >
          <Plus size={18} />
          Create session
        </button>
      </section>

      <ErrorBox message={error} />

      <section className="stats">
        {cards.map(
          ([label, value, Icon, tone]) => (
            <article key={label}>
              <span
                className={`stat-icon ${tone}`}
              >
                <Icon />
              </span>

              <div>
                <small>{label}</small>
                <strong>{value}</strong>
              </div>
            </article>
          )
        )}
      </section>

      <section className="grid-two">
        <article className="panel">
          <div className="panel-head">
            <div>
              <p className="eyebrow">
                Live operations
              </p>

              <h3>Academic activity</h3>
            </div>
          </div>

          <div className="operation-grid">
            <div>
              <BookOpen />
              <strong>{summary.courses}</strong>
              <span>Courses</span>
            </div>

            <div>
              <CalendarDays />
              <strong>{summary.sessions}</strong>
              <span>Sessions</span>
            </div>

            <div>
              <ShieldCheck />

              <strong>
                {summary.open_fraud_alerts}
              </strong>

              <span>Open alerts</span>
            </div>
          </div>
        </article>

        <article className="panel">
          <div className="panel-head">
            <div>
              <p className="eyebrow">
                Requires attention
              </p>

              <h3>Recent fraud alerts</h3>
            </div>

            <button
              className="text-btn"
              onClick={() => navigate("alerts")}
            >
              View all
              <ChevronRight size={16} />
            </button>
          </div>

          {alerts.length ? (
            alerts.map((alert) => (
              <div
                className="alert-row"
                key={alert.id}
              >
                <span className="risk">
                  {Math.round(
                    alert.risk_score * 100
                  )}
                </span>

                <div>
                  <strong>
                    {alert.student_name}
                  </strong>

                  <small>
                    {alert.course_code} ·{" "}
                    {alert.session_title}
                  </small>
                </div>

                <Status
                  value={alert.review_status}
                />
              </div>
            ))
          ) : (
            <Empty
              icon={ShieldCheck}
              title="No open alerts"
              text="All attendance events are currently resolved."
            />
          )}
        </article>
      </section>
    </>
  );
}

function Courses({ user }) {
  const [items, setItems] = useState([]);
  const [lecturers, setLecturers] =
    useState([]);

  const [form, setForm] = useState({
    code: "",
    title: "",
    lecturer: "",
  });

  const [show, setShow] = useState(false);
  const [error, setError] = useState("");

  const load = useCallback(() => {
    return Promise.all([
      api("/attendance/courses/"),
      api("/auth/lecturers/"),
    ])
      .then(([courseList, lecturerList]) => {
        setItems(courseList);
        setLecturers(lecturerList);
      })
      .catch((err) => setError(err.message));
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  async function save(event) {
    event.preventDefault();
    setError("");

    try {
      await api("/attendance/courses/", {
        method: "POST",
        body: JSON.stringify(form),
      });

      setShow(false);

      setForm({
        code: "",
        title: "",
        lecturer: "",
      });

      load();
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <>
      <PageHead
        eyebrow="Academic structure"
        title="Courses"
        text="Create courses and view ownership and enrolment totals."
        action={() => setShow(!show)}
        actionText="New course"
      />

      <ErrorBox message={error} />

      {show && (
        <form
          className="inline-form panel"
          onSubmit={save}
        >
          <Field
            label="Course code"
            value={form.code}
            set={(value) =>
              setForm({
                ...form,
                code: value,
              })
            }
            placeholder="CSC401"
          />

          <Field
            label="Course title"
            value={form.title}
            set={(value) =>
              setForm({
                ...form,
                title: value,
              })
            }
            placeholder="Artificial Intelligence"
          />

          {user.role === "admin" && (
            <Select
              label="Lecturer"
              value={form.lecturer}
              set={(value) =>
                setForm({
                  ...form,
                  lecturer: value,
                })
              }
              options={lecturers.map(
                (lecturer) => [
                  lecturer.id,
                  lecturer.full_name,
                ]
              )}
            />
          )}

          <button className="primary">
            Save course
          </button>
        </form>
      )}

      <div className="panel table-panel">
        {items.length ? (
          <table>
            <thead>
              <tr>
                <th>Course</th>
                <th>Title</th>
                <th>Lecturer</th>
                <th>Students</th>
              </tr>
            </thead>

            <tbody>
              {items.map((course) => (
                <tr key={course.id}>
                  <td>
                    <strong>
                      {course.code}
                    </strong>
                  </td>

                  <td>{course.title}</td>
                  <td>{course.lecturer_name}</td>
                  <td>{course.student_count}</td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <Empty
            icon={BookOpen}
            title="No courses yet"
            text="Create the first course to begin organising attendance."
          />
        )}
      </div>
    </>
  );
}

function Sessions() {
  const [items, setItems] = useState([]);
  const [courses, setCourses] =
    useState([]);

  const [show, setShow] = useState(false);
  const [error, setError] = useState("");

  const [selectedSession, setSelectedSession] =
    useState(null);

  const [
    attendanceRegister,
    setAttendanceRegister,
  ] = useState([]);

  const [registerLoading, setRegisterLoading] =
    useState(false);

  const initialForm = {
    course: "",
    title: "",
    starts_at: "",
    ends_at: "",
    latitude: "",
    longitude: "",
    radius_metres: 100,
    minimum_dwell_seconds: 30,
  };

  const [form, setForm] =
    useState(initialForm);

  const load = useCallback(() => {
    return Promise.all([
      api("/attendance/sessions/"),
      api("/attendance/courses/"),
    ])
      .then(([sessionList, courseList]) => {
        setItems(sessionList);
        setCourses(courseList);
      })
      .catch((err) => setError(err.message));
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  async function save(event) {
    event.preventDefault();
    setError("");

    try {
      await api("/attendance/sessions/", {
        method: "POST",
        body: JSON.stringify({
          ...form,
          starts_at: new Date(
            form.starts_at
          ).toISOString(),
          ends_at: new Date(
            form.ends_at
          ).toISOString(),
          latitude: Number(form.latitude),
          longitude: Number(form.longitude),
          radius_metres: Number(
            form.radius_metres
          ),
          minimum_dwell_seconds: Number(
            form.minimum_dwell_seconds
          ),
        }),
      });

      setShow(false);
      setForm(initialForm);
      load();
    } catch (err) {
      setError(err.message);
    }
  }

  async function openAttendanceRegister(
    session
  ) {
    setSelectedSession(session);
    setAttendanceRegister([]);
    setRegisterLoading(true);
    setError("");

    try {
      const [
        attendanceRecords,
        enrolments,
      ] = await Promise.all([
        api(
          `/attendance/attendance/history/?session=${session.id}`
        ),
        api(
          `/attendance/enrollments/?course=${session.course}`
        ),
      ]);

      const recordsByStudent = new Map();

      attendanceRecords.forEach((record) => {
        recordsByStudent.set(
          record.student,
          record
        );
      });

      const completeRegister =
        enrolments.map((enrolment) => ({
          enrolment,
          record:
            recordsByStudent.get(
              enrolment.student
            ) || null,
        }));

      setAttendanceRegister(
        completeRegister
      );

      window.scrollTo({
        top: 0,
        behavior: "smooth",
      });
    } catch (err) {
      setError(err.message);
    } finally {
      setRegisterLoading(false);
    }
  }

  const confirmedTotal =
    attendanceRegister.filter(
      (item) =>
        item.record?.status === "confirmed"
    ).length;

  const pendingTotal =
    attendanceRegister.filter(
      (item) =>
        item.record?.status ===
        "pending_review"
    ).length;

  const rejectedTotal =
    attendanceRegister.filter(
      (item) =>
        item.record?.status === "rejected"
    ).length;

  const absentTotal =
    attendanceRegister.filter(
      (item) => !item.record
    ).length;

  return (
    <>
      <PageHead
        eyebrow="Attendance windows"
        title="Class sessions"
        text="Schedule attendance events and click a session to view its attendance register."
        action={() => setShow(!show)}
        actionText="New session"
      />

      <ErrorBox message={error} />

      {show && (
        <form
          className="form-grid panel"
          onSubmit={save}
        >
          <Select
            label="Course"
            value={form.course}
            set={(value) =>
              setForm({
                ...form,
                course: value,
              })
            }
            options={courses.map(
              (course) => [
                course.id,
                `${course.code} — ${course.title}`,
              ]
            )}
          />

          <Field
            label="Session title"
            value={form.title}
            set={(value) =>
              setForm({
                ...form,
                title: value,
              })
            }
          />

          <Field
            label="Starts"
            type="datetime-local"
            value={form.starts_at}
            set={(value) =>
              setForm({
                ...form,
                starts_at: value,
              })
            }
          />

          <Field
            label="Ends"
            type="datetime-local"
            value={form.ends_at}
            set={(value) =>
              setForm({
                ...form,
                ends_at: value,
              })
            }
          />

          <Field
            label="Latitude"
            type="number"
            value={form.latitude}
            set={(value) =>
              setForm({
                ...form,
                latitude: value,
              })
            }
          />

          <Field
            label="Longitude"
            type="number"
            value={form.longitude}
            set={(value) =>
              setForm({
                ...form,
                longitude: value,
              })
            }
          />

          <Field
            label="Radius (metres)"
            type="number"
            value={form.radius_metres}
            set={(value) =>
              setForm({
                ...form,
                radius_metres: value,
              })
            }
          />

          <Field
            label="Dwell time (seconds)"
            type="number"
            value={
              form.minimum_dwell_seconds
            }
            set={(value) =>
              setForm({
                ...form,
                minimum_dwell_seconds:
                  value,
              })
            }
          />

          <button className="primary">
            Create session
          </button>
        </form>
      )}

      {selectedSession && (
        <section
          className="panel"
          style={{
            marginBottom: "22px",
          }}
        >
          <div className="panel-head">
            <div>
              <p className="eyebrow">
                Session attendance register
              </p>

              <h3>
                {selectedSession.course_code}
                {" — "}
                {selectedSession.title}
              </h3>

              <p
                style={{
                  color: "#6c7887",
                  fontSize: "12px",
                  margin: "6px 0 0",
                }}
              >
                {new Date(
                  selectedSession.starts_at
                ).toLocaleString()}
              </p>
            </div>

            <button
              type="button"
              className="text-btn"
              onClick={() => {
                setSelectedSession(null);
                setAttendanceRegister([]);
              }}
            >
              Close register
              <XCircle size={16} />
            </button>
          </div>

          {registerLoading ? (
            <Loading />
          ) : (
            <>
              <section
                className="stats"
                style={{
                  marginBottom: "20px",
                }}
              >
                <article>
                  <span className="stat-icon navy">
                    <Users />
                  </span>

                  <div>
                    <small>
                      Enrolled students
                    </small>

                    <strong>
                      {
                        attendanceRegister.length
                      }
                    </strong>
                  </div>
                </article>

                <article>
                  <span className="stat-icon green">
                    <CheckCircle2 />
                  </span>

                  <div>
                    <small>Confirmed</small>
                    <strong>
                      {confirmedTotal}
                    </strong>
                  </div>
                </article>

                <article>
                  <span className="stat-icon amber">
                    <AlertTriangle />
                  </span>

                  <div>
                    <small>Pending review</small>
                    <strong>
                      {pendingTotal}
                    </strong>
                  </div>
                </article>

                <article>
                  <span className="stat-icon red">
                    <XCircle />
                  </span>

                  <div>
                    <small>Absent</small>
                    <strong>
                      {absentTotal}
                    </strong>
                  </div>
                </article>
              </section>

              <div
                style={{
                  marginBottom: "14px",
                  color: "#6c7887",
                  fontSize: "12px",
                }}
              >
                Rejected attendance attempts:{" "}
                <strong>{rejectedTotal}</strong>
              </div>

              <div className="table-panel">
                {attendanceRegister.length >
                0 ? (
                  <table>
                    <thead>
                      <tr>
                        <th>Student</th>
                        <th>
                          Matric number
                        </th>
                        <th>
                          Check-in time
                        </th>
                        <th>Status</th>
                      </tr>
                    </thead>

                    <tbody>
                      {attendanceRegister.map(
                        ({
                          enrolment,
                          record,
                        }) => (
                          <tr
                            key={enrolment.id}
                          >
                            <td>
                              <strong>
                                {
                                  enrolment
                                    .student_details
                                    .full_name
                                }
                              </strong>
                            </td>

                            <td>
                              {
                                enrolment
                                  .student_details
                                  .matric_number
                              }
                            </td>

                            <td>
                              {record
                                ? new Date(
                                    record.checked_in_at
                                  ).toLocaleString()
                                : "No check-in"}
                            </td>

                            <td>
                              {record ? (
                                <Status
                                  value={
                                    record.status
                                  }
                                />
                              ) : (
                                <span className="status rejected">
                                  Absent
                                </span>
                              )}
                            </td>
                          </tr>
                        )
                      )}
                    </tbody>
                  </table>
                ) : (
                  <Empty
                    icon={Users}
                    title="No enrolled students"
                    text="No students are currently enrolled in this course."
                  />
                )}
              </div>
            </>
          )}
        </section>
      )}

      <div className="cards-list">
        {items.length ? (
          items.map((session) => (
            <article
              className="session-card"
              key={session.id}
              onClick={() =>
                openAttendanceRegister(
                  session
                )
              }
              style={{
                cursor: "pointer",
                alignItems: "center",
                borderColor:
                  selectedSession?.id ===
                  session.id
                    ? "#2c72c7"
                    : undefined,
                boxShadow:
                  selectedSession?.id ===
                  session.id
                    ? "0 0 0 3px rgba(44, 114, 199, 0.1)"
                    : undefined,
              }}
            >
              <div className="date-block">
                <strong>
                  {new Date(
                    session.starts_at
                  ).getDate()}
                </strong>

                <span>
                  {new Date(
                    session.starts_at
                  ).toLocaleString("en", {
                    month: "short",
                  })}
                </span>
              </div>

              <div className="grow">
                <div className="card-title">
                  <Status
                    value={
                      session.is_active
                        ? "active"
                        : "scheduled"
                    }
                  />

                  <small>
                    {session.course_code}
                  </small>
                </div>

                <h3>{session.title}</h3>

                <p>
                  <CalendarDays size={16} />

                  {new Date(
                    session.starts_at
                  ).toLocaleString()}
                  {" – "}

                  {new Date(
                    session.ends_at
                  ).toLocaleTimeString(
                    [],
                    {
                      hour: "2-digit",
                      minute: "2-digit",
                    }
                  )}
                </p>

                <p>
                  <MapPin size={16} />

                  {session.radius_metres}m
                  geofence ·{" "}
                  {
                    session.minimum_dwell_seconds
                  }
                  s dwell
                </p>
              </div>

              <button
                type="button"
                className="text-btn"
                onClick={(event) => {
                  event.stopPropagation();

                  openAttendanceRegister(
                    session
                  );
                }}
              >
                View attendance
                <ChevronRight size={18} />
              </button>
            </article>
          ))
        ) : (
          <div className="panel">
            <Empty
              icon={CalendarDays}
              title="No sessions scheduled"
              text="Create a session to open a time-bound attendance window."
            />
          </div>
        )}
      </div>
    </>
  );
}

function Enrolments() {
  const [items, setItems] = useState([]);
  const [students, setStudents] =
    useState([]);

  const [courses, setCourses] =
    useState([]);

  const [form, setForm] = useState({
    student: "",
    course: "",
  });

  const [error, setError] = useState("");

  const load = useCallback(() => {
    return Promise.all([
      api("/attendance/enrollments/"),
      api("/auth/students/"),
      api("/attendance/courses/"),
    ])
      .then(
        ([
          enrolmentList,
          studentList,
          courseList,
        ]) => {
          setItems(enrolmentList);
          setStudents(studentList);
          setCourses(courseList);
        }
      )
      .catch((err) => setError(err.message));
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  async function save(event) {
    event.preventDefault();
    setError("");

    try {
      await api(
        "/attendance/enrollments/",
        {
          method: "POST",
          body: JSON.stringify(form),
        }
      );

      setForm({
        student: "",
        course: "",
      });

      load();
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <>
      <PageHead
        eyebrow="Course participation"
        title="Student enrolments"
        text="Assign registered students to the correct courses."
      />

      <ErrorBox message={error} />

      <form
        className="inline-form panel"
        onSubmit={save}
      >
        <Select
          label="Student"
          value={form.student}
          set={(value) =>
            setForm({
              ...form,
              student: value,
            })
          }
          options={students.map(
            (student) => [
              student.id,
              `${student.full_name} — ${student.matric_number}`,
            ]
          )}
        />

        <Select
          label="Course"
          value={form.course}
          set={(value) =>
            setForm({
              ...form,
              course: value,
            })
          }
          options={courses.map(
            (course) => [
              course.id,
              `${course.code} — ${course.title}`,
            ]
          )}
        />

        <button className="primary">
          <UserRoundPlus size={18} />
          Enrol student
        </button>
      </form>

      <div className="panel table-panel">
        {items.length ? (
          <table>
            <thead>
              <tr>
                <th>Student</th>
                <th>Matric number</th>
                <th>Course</th>
                <th>Enrolled</th>
              </tr>
            </thead>

            <tbody>
              {items.map((enrolment) => (
                <tr key={enrolment.id}>
                  <td>
                    <strong>
                      {
                        enrolment
                          .student_details
                          .full_name
                      }
                    </strong>
                  </td>

                  <td>
                    {
                      enrolment
                        .student_details
                        .matric_number
                    }
                  </td>

                  <td>
                    {enrolment.course_code}
                  </td>

                  <td>
                    {new Date(
                      enrolment.enrolled_at
                    ).toLocaleDateString()}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <Empty
            icon={Users}
            title="No enrolments"
            text="Use the form above to enrol a student."
          />
        )}
      </div>
    </>
  );
}

function Alerts() {
  const [items, setItems] = useState([]);
  const [error, setError] = useState("");
  const [note, setNote] = useState({});

  const load = useCallback(() => {
    return api(
      "/attendance/fraud-alerts/"
    )
      .then(setItems)
      .catch((err) => setError(err.message));
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  async function review(id, decision) {
    setError("");

    try {
      await api(
        `/attendance/fraud-alerts/${id}/review/`,
        {
          method: "POST",
          body: JSON.stringify({
            decision,
            review_note:
              note[id] ||
              "Reviewed against the available attendance evidence.",
          }),
        }
      );

      load();
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <>
      <PageHead
        eyebrow="Human-governed decisions"
        title="Fraud review"
        text="Inspect explainable risk evidence before resolving a flagged attendance event."
      />

      <ErrorBox message={error} />

      <div className="review-list">
        {items.length ? (
          items.map((alert) => (
            <article
              className="review-card"
              key={alert.id}
            >
              <div className="risk-panel">
                <span>Risk score</span>

                <strong>
                  {Math.round(
                    alert.risk_score * 100
                  )}

                  <small>%</small>
                </strong>

                <Status
                  value={
                    alert.review_status
                  }
                />
              </div>

              <div className="review-main">
                <div className="panel-head">
                  <div>
                    <h3>
                      {alert.student_name}
                    </h3>

                    <p>
                      {alert.matric_number} ·{" "}
                      {alert.course_code} ·{" "}
                      {alert.session_title}
                    </p>
                  </div>
                </div>

                <p className="reason-title">
                  Why this event was flagged
                </p>

                <ul>
                  {alert.reasons.map(
                    (reason, index) => (
                      <li key={index}>
                        <AlertTriangle
                          size={16}
                        />

                        {reason}
                      </li>
                    )
                  )}
                </ul>

                {alert.review_status ===
                  "open" && (
                  <div className="review-actions">
                    <input
                      value={
                        note[alert.id] || ""
                      }
                      onChange={(event) =>
                        setNote({
                          ...note,
                          [alert.id]:
                            event.target.value,
                        })
                      }
                      placeholder="Add a review note…"
                    />

                    <button
                      className="approve"
                      onClick={() =>
                        review(
                          alert.id,
                          "approved"
                        )
                      }
                    >
                      <CheckCircle2
                        size={17}
                      />
                      Approve
                    </button>

                    <button
                      className="reject"
                      onClick={() =>
                        review(
                          alert.id,
                          "rejected"
                        )
                      }
                    >
                      <XCircle size={17} />
                      Reject
                    </button>
                  </div>
                )}
              </div>
            </article>
          ))
        ) : (
          <div className="panel">
            <Empty
              icon={ShieldCheck}
              title="No fraud alerts"
              text="Flagged events will appear here with clear supporting reasons."
            />
          </div>
        )}
      </div>
    </>
  );
}

function Reports() {
  const [error, setError] = useState("");

  async function download() {
    setError("");

    try {
      await downloadReport();
    } catch (err) {
      setError(err.message);
    }
  }

  return (
    <>
      <PageHead
        eyebrow="Institutional reporting"
        title="Attendance reports"
        text="Export traceable attendance evidence for analysis and record keeping."
      />

      <ErrorBox message={error} />

      <section className="report-card">
        <div className="report-icon">
          <Download />
        </div>

        <div>
          <h3>
            Complete attendance register
          </h3>

          <p>
            Includes student identity, course,
            session, check-in time, final status,
            risk score and decision explanation.
          </p>

          <span>
            CSV format · Compatible with Excel
          </span>
        </div>

        <button
          className="primary"
          onClick={download}
        >
          <Download size={18} />
          Download CSV
        </button>
      </section>

      <div className="info-banner">
        <ShieldCheck />

        <div>
          <strong>
            Privacy-aware reporting
          </strong>

          <p>
            Reports include attendance evidence
            only. Continuous student movement is
            never collected.
          </p>
        </div>
      </div>
    </>
  );
}

function PageHead({
  eyebrow,
  title,
  text,
  action,
  actionText,
}) {
  return (
    <section className="page-head">
      <div>
        <p className="eyebrow">{eyebrow}</p>
        <h1>{title}</h1>
        <p>{text}</p>
      </div>

      {action && (
        <button
          className="primary"
          onClick={action}
        >
          <Plus size={18} />
          {actionText}
        </button>
      )}
    </section>
  );
}

function Field({
  label,
  value,
  set,
  type = "text",
  placeholder = "",
}) {
  return (
    <label>
      {label}

      <input
        required
        type={type}
        step={
          type === "number"
            ? "any"
            : undefined
        }
        value={value}
        onChange={(event) =>
          set(event.target.value)
        }
        placeholder={placeholder}
      />
    </label>
  );
}

function Select({
  label,
  value,
  set,
  options,
}) {
  return (
    <label>
      {label}

      <select
        required
        value={value}
        onChange={(event) =>
          set(event.target.value)
        }
      >
        <option value="">
          Select {label.toLowerCase()}
        </option>

        {options.map(([id, name]) => (
          <option
            value={id}
            key={id}
          >
            {name}
          </option>
        ))}
      </select>
    </label>
  );
}

export default function App() {
  const [user, setUser] = useState(() => {
    try {
      return JSON.parse(
        localStorage.getItem(
          "attendai_user"
        )
      );
    } catch {
      return null;
    }
  });

  function signOut() {
    logout();
    setUser(null);
  }

  return getToken() && user ? (
    <Shell
      user={user}
      onLogout={signOut}
    />
  ) : (
    <Login onLogin={setUser} />
  );
}