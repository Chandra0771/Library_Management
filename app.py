from flask import Flask, request, jsonify, render_template_string
import sqlite3, os

app = Flask(__name__)
DB = "library.db"

# ── Database setup ──────────────────────────────────────────────
def get_db():
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    return con

SEED_BOOKS = [
    (1,  "Wings of Fire",              "A.P.J. Abdul Kalam",       299,  12),
    (2,  "The Alchemist",              "Paulo Coelho",             350,   8),
    (3,  "Atomic Habits",              "James Clear",              499,  15),
    (4,  "Rich Dad Poor Dad",          "Robert T. Kiyosaki",       320,   6),
    (5,  "Ikigai",                     "Héctor García",            240,   9),
    (6,  "The Power of Your Subconscious Mind", "Joseph Murphy",   199,  11),
    (7,  "Think and Grow Rich",        "Napoleon Hill",            249,  10),
    (8,  "Deep Work",                  "Cal Newport",              449,   7),
    (9,  "Sapiens",                    "Yuval Noah Harari",        599,   5),
    (10, "1984",                       "George Orwell",            199,  14),
    (11, "To Kill a Mockingbird",      "Harper Lee",               299,   8),
    (12, "The Great Gatsby",           "F. Scott Fitzgerald",      249,  10),
    (13, "Harry Potter & Sorcerer's Stone", "J.K. Rowling",        399,  20),
    (14, "The Diary of a Young Girl",  "Anne Frank",               249,   9),
    (15, "Man's Search for Meaning",   "Viktor E. Frankl",         299,  13),
    (16, "Zero to One",                "Peter Thiel",              499,   6),
    (17, "The 7 Habits of Highly Effective People", "Stephen Covey", 399, 8),
    (18, "Shoe Dog",                   "Phil Knight",              549,   5),
    (19, "A Brief History of Time",    "Stephen Hawking",          399,   7),
    (20, "The Monk Who Sold His Ferrari", "Robin Sharma",          299,  11),
]

def init_db():
    with get_db() as con:
        con.execute("""
            CREATE TABLE IF NOT EXISTS book (
                bno    INTEGER PRIMARY KEY,
                bname  TEXT    NOT NULL,
                bauth  TEXT    NOT NULL,
                bprice INTEGER NOT NULL,
                bqty   INTEGER NOT NULL
            )
        """)
        # Only seed if table is empty
        count = con.execute("SELECT COUNT(*) FROM book").fetchone()[0]
        if count == 0:
            con.executemany("INSERT INTO book VALUES (?,?,?,?,?)", SEED_BOOKS)
            print(f"  Seeded {len(SEED_BOOKS)} books into the library.")
        con.commit()

# ── API routes ──────────────────────────────────────────────────
@app.route("/api/books", methods=["GET"])
def get_books():
    with get_db() as con:
        rows = con.execute("SELECT * FROM book ORDER BY bno").fetchall()
    return jsonify([dict(r) for r in rows])

@app.route("/api/books", methods=["POST"])
def add_book():
    d = request.json
    try:
        with get_db() as con:
            con.execute("INSERT INTO book VALUES (?,?,?,?,?)",
                        (d["bno"], d["bname"], d["bauth"], d["bprice"], d["bqty"]))
            con.commit()
        return jsonify({"ok": True})
    except sqlite3.IntegrityError:
        return jsonify({"ok": False, "error": "Book Code already exists."}), 409

@app.route("/api/books/<int:bno>", methods=["PUT"])
def update_book(bno):
    d = request.json
    with get_db() as con:
        con.execute("UPDATE book SET bname=?,bauth=?,bprice=?,bqty=? WHERE bno=?",
                    (d["bname"], d["bauth"], d["bprice"], d["bqty"], bno))
        con.commit()
    return jsonify({"ok": True})

@app.route("/api/books/<int:bno>", methods=["DELETE"])
def delete_book(bno):
    with get_db() as con:
        con.execute("DELETE FROM book WHERE bno=?", (bno,))
        con.commit()
    return jsonify({"ok": True})

# ── Frontend ────────────────────────────────────────────────────
HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>Library Manager</title>
<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:wght@400;500;600&family=DM+Sans:wght@300;400;500&display=swap" rel="stylesheet"/>
<style>
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

  :root {
    --glass:        rgba(255,255,255,0.12);
    --glass-border: rgba(255,255,255,0.22);
    --glass-hover:  rgba(255,255,255,0.20);
    --glass-strong: rgba(255,255,255,0.26);
    --text-main:    rgba(255,255,255,0.95);
    --text-muted:   rgba(255,255,255,0.60);
    --text-soft:    rgba(255,255,255,0.80);
    --accent:       #c9a96e;
    --accent-glow:  rgba(201,169,110,0.35);
    --danger:       rgba(255,100,100,0.85);
    --success:      rgba(100,220,160,0.85);
    --radius:       18px;
    --radius-sm:    10px;
  }

  body {
    min-height: 100vh;
    font-family: 'DM Sans', sans-serif;
    font-size: 14px;
    color: var(--text-main);
    background: #0f0c1a;
    background-image:
      radial-gradient(ellipse 80% 60% at 20% 10%, #2a1a5e 0%, transparent 60%),
      radial-gradient(ellipse 60% 50% at 80% 80%, #1a3050 0%, transparent 55%),
      radial-gradient(ellipse 50% 40% at 60% 30%, #3d1f5c 0%, transparent 50%);
    overflow-x: hidden;
  }

  /* Floating orbs */
  .orb { position: fixed; border-radius: 50%; filter: blur(80px); pointer-events: none; z-index: 0; }
  .orb-1 { width: 500px; height: 500px; background: rgba(120,60,200,0.18); top: -100px; left: -100px; }
  .orb-2 { width: 400px; height: 400px; background: rgba(40,100,200,0.15); bottom: -80px; right: -80px; }
  .orb-3 { width: 300px; height: 300px; background: rgba(200,150,60,0.12); top: 50%; left: 50%; transform: translate(-50%,-50%); }

  .app { position: relative; z-index: 1; max-width: 1100px; margin: 0 auto; padding: 40px 24px 80px; }

  /* Header */
  .header { text-align: center; margin-bottom: 52px; }
  .header-icon {
    width: 64px; height: 64px; margin: 0 auto 20px;
    background: var(--glass-strong);
    backdrop-filter: blur(20px);
    border: 1px solid var(--glass-border);
    border-radius: 20px;
    display: flex; align-items: center; justify-content: center;
    font-size: 28px;
  }
  .header h1 {
    font-family: 'Cormorant Garamond', serif;
    font-size: 42px; font-weight: 600; letter-spacing: -0.5px;
    background: linear-gradient(135deg, #fff 30%, var(--accent) 100%);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
  }
  .header p { color: var(--text-muted); margin-top: 8px; font-weight: 300; letter-spacing: 0.5px; }

  /* Stats bar */
  .stats { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; margin-bottom: 36px; }
  .stat-card {
    background: var(--glass); backdrop-filter: blur(20px);
    border: 1px solid var(--glass-border); border-radius: var(--radius);
    padding: 20px 24px;
    transition: background 0.2s;
  }
  .stat-card:hover { background: var(--glass-hover); }
  .stat-label { font-size: 11px; text-transform: uppercase; letter-spacing: 1.5px; color: var(--text-muted); margin-bottom: 8px; }
  .stat-value { font-family: 'Cormorant Garamond', serif; font-size: 32px; font-weight: 600; color: var(--accent); }

  /* Main layout */
  .layout { display: grid; grid-template-columns: 340px 1fr; gap: 24px; align-items: start; }
  @media (max-width: 760px) { .layout { grid-template-columns: 1fr; } }

  /* Glass panel */
  .panel {
    background: var(--glass); backdrop-filter: blur(24px);
    border: 1px solid var(--glass-border); border-radius: var(--radius);
    overflow: hidden;
  }
  .panel-header {
    padding: 20px 24px 16px;
    border-bottom: 1px solid rgba(255,255,255,0.08);
    display: flex; align-items: center; justify-content: space-between;
  }
  .panel-title {
    font-family: 'Cormorant Garamond', serif;
    font-size: 20px; font-weight: 500; color: var(--text-main);
  }
  .panel-body { padding: 24px; }

  /* Form */
  .form-grid { display: grid; gap: 14px; }
  .form-row { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; }
  .field label {
    display: block; font-size: 11px; text-transform: uppercase;
    letter-spacing: 1.2px; color: var(--text-muted); margin-bottom: 7px;
  }
  .field input {
    width: 100%; padding: 11px 14px;
    background: rgba(255,255,255,0.07);
    border: 1px solid rgba(255,255,255,0.15);
    border-radius: var(--radius-sm);
    color: var(--text-main); font-family: inherit; font-size: 14px;
    outline: none; transition: border-color 0.2s, background 0.2s;
  }
  .field input:focus {
    border-color: var(--accent);
    background: rgba(255,255,255,0.11);
  }
  .field input::placeholder { color: rgba(255,255,255,0.25); }

  /* Buttons */
  .btn {
    padding: 11px 22px; border-radius: var(--radius-sm);
    font-family: inherit; font-size: 13px; font-weight: 500;
    cursor: pointer; border: none; transition: all 0.2s; letter-spacing: 0.3px;
  }
  .btn-primary {
    background: linear-gradient(135deg, var(--accent) 0%, #a07840 100%);
    color: #1a1000; width: 100%; margin-top: 6px; padding: 13px;
    box-shadow: 0 4px 20px var(--accent-glow);
  }
  .btn-primary:hover { filter: brightness(1.1); transform: translateY(-1px); box-shadow: 0 6px 28px var(--accent-glow); }
  .btn-primary:active { transform: translateY(0); }
  .btn-glass {
    background: var(--glass); border: 1px solid var(--glass-border);
    color: var(--text-soft);
  }
  .btn-glass:hover { background: var(--glass-hover); }
  .btn-icon {
    padding: 7px 10px; font-size: 13px; border-radius: 8px;
    background: transparent; border: 1px solid transparent;
    color: var(--text-muted); cursor: pointer;
    transition: all 0.15s;
  }
  .btn-icon:hover { background: rgba(255,255,255,0.1); color: var(--text-main); border-color: var(--glass-border); }
  .btn-icon.danger:hover { background: rgba(255,80,80,0.2); color: #ff8080; border-color: rgba(255,80,80,0.3); }

  /* Search bar */
  .search-wrap { padding: 16px 24px; border-bottom: 1px solid rgba(255,255,255,0.08); }
  .search-input {
    width: 100%; padding: 10px 16px 10px 38px;
    background: rgba(255,255,255,0.07); border: 1px solid rgba(255,255,255,0.12);
    border-radius: 10px; color: var(--text-main); font-family: inherit; font-size: 13px;
    outline: none; transition: border-color 0.2s; background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='14' height='14' viewBox='0 0 24 24' fill='none' stroke='rgba(255,255,255,0.4)' stroke-width='2'%3E%3Ccircle cx='11' cy='11' r='8'/%3E%3Cpath d='m21 21-4.35-4.35'/%3E%3C/svg%3E");
    background-repeat: no-repeat; background-position: 12px center;
  }
  .search-input:focus { border-color: var(--accent); }
  .search-input::placeholder { color: rgba(255,255,255,0.25); }

  /* Book list */
  .book-list { max-height: 540px; overflow-y: auto; }
  .book-list::-webkit-scrollbar { width: 4px; }
  .book-list::-webkit-scrollbar-track { background: transparent; }
  .book-list::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.15); border-radius: 2px; }

  .book-item {
    display: flex; align-items: center; gap: 14px;
    padding: 14px 24px; border-bottom: 1px solid rgba(255,255,255,0.05);
    transition: background 0.15s; cursor: pointer;
  }
  .book-item:last-child { border-bottom: none; }
  .book-item:hover { background: rgba(255,255,255,0.06); }
  .book-item.selected { background: rgba(201,169,110,0.12); border-left: 2px solid var(--accent); }

  .book-avatar {
    width: 38px; height: 38px; flex-shrink: 0;
    background: linear-gradient(135deg, rgba(120,60,200,0.5), rgba(40,100,200,0.5));
    border-radius: 10px; border: 1px solid rgba(255,255,255,0.15);
    display: flex; align-items: center; justify-content: center;
    font-family: 'Cormorant Garamond', serif; font-size: 16px; font-weight: 600; color: #fff;
  }
  .book-info { flex: 1; min-width: 0; }
  .book-name { font-size: 14px; font-weight: 500; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
  .book-author { font-size: 12px; color: var(--text-muted); margin-top: 2px; }
  .book-meta { display: flex; align-items: center; gap: 10px; flex-shrink: 0; }
  .badge {
    font-size: 11px; padding: 3px 8px; border-radius: 6px; font-weight: 500;
    background: rgba(201,169,110,0.15); color: var(--accent);
    border: 1px solid rgba(201,169,110,0.25);
  }
  .badge.qty { background: rgba(100,200,160,0.12); color: #80e0b0; border-color: rgba(100,200,160,0.2); }

  .empty {
    padding: 60px 24px; text-align: center; color: var(--text-muted);
  }
  .empty-icon { font-size: 36px; margin-bottom: 12px; opacity: 0.4; }
  .empty p { font-size: 13px; }

  /* Toast */
  .toast-wrap { position: fixed; top: 28px; right: 28px; z-index: 100; display: flex; flex-direction: column; gap: 10px; }
  .toast {
    padding: 12px 18px; border-radius: 12px; font-size: 13px;
    backdrop-filter: blur(20px); border: 1px solid;
    animation: slideIn 0.3s ease; pointer-events: none;
    max-width: 280px;
  }
  .toast.success { background: rgba(60,160,110,0.25); border-color: rgba(100,220,160,0.4); color: #a0ffd0; }
  .toast.error   { background: rgba(160,60,60,0.25);  border-color: rgba(255,100,100,0.4); color: #ffb0b0; }
  @keyframes slideIn { from { opacity:0; transform: translateX(20px); } to { opacity:1; transform: translateX(0); } }

  /* Edit mode badge */
  .edit-badge {
    font-size: 11px; padding: 3px 10px; border-radius: 6px;
    background: rgba(201,169,110,0.2); color: var(--accent);
    border: 1px solid rgba(201,169,110,0.35); font-weight: 500;
  }
  .cancel-btn {
    background: none; border: none; color: var(--text-muted);
    font-size: 18px; cursor: pointer; padding: 0 4px; line-height: 1;
  }
  .cancel-btn:hover { color: var(--text-main); }
</style>
</head>
<body>

<div class="orb orb-1"></div>
<div class="orb orb-2"></div>
<div class="orb orb-3"></div>
<div class="toast-wrap" id="toasts"></div>

<div class="app">

  <div class="header">
    <div class="header-icon">📚</div>
    <h1>Library Manager</h1>
    <p>Book record management system</p>
  </div>

  <div class="stats">
    <div class="stat-card">
      <div class="stat-label">Total Books</div>
      <div class="stat-value" id="stat-count">0</div>
    </div>
    <div class="stat-card">
      <div class="stat-label">Total Stock</div>
      <div class="stat-value" id="stat-qty">0</div>
    </div>
    <div class="stat-card">
      <div class="stat-label">Avg Price</div>
      <div class="stat-value" id="stat-price">₹0</div>
    </div>
  </div>

  <div class="layout">

    <!-- Form panel -->
    <div class="panel">
      <div class="panel-header">
        <span class="panel-title" id="form-title">Add Book</span>
        <div style="display:flex;align-items:center;gap:8px;">
          <span class="edit-badge" id="edit-badge" style="display:none;">Editing</span>
          <button class="cancel-btn" id="cancel-btn" style="display:none;" title="Cancel edit">✕</button>
        </div>
      </div>
      <div class="panel-body">
        <div class="form-grid">
          <div class="field">
            <label>Book Code</label>
            <input type="number" id="f-bno" placeholder="e.g. 101"/>
          </div>
          <div class="field">
            <label>Book Name</label>
            <input type="text" id="f-bname" placeholder="e.g. Wings of Fire"/>
          </div>
          <div class="field">
            <label>Author</label>
            <input type="text" id="f-bauth" placeholder="e.g. A.P.J. Abdul Kalam"/>
          </div>
          <div class="form-row">
            <div class="field">
              <label>Price (₹)</label>
              <input type="number" id="f-bprice" placeholder="299"/>
            </div>
            <div class="field">
              <label>Quantity</label>
              <input type="number" id="f-bqty" placeholder="10"/>
            </div>
          </div>
          <button class="btn btn-primary" id="submit-btn" onclick="submitForm()">Add Book</button>
        </div>
      </div>
    </div>

    <!-- Book list panel -->
    <div class="panel">
      <div class="panel-header">
        <span class="panel-title">All Books</span>
      </div>
      <div class="search-wrap">
        <input class="search-input" type="text" placeholder="Search by title or author…" oninput="filterBooks(this.value)"/>
      </div>
      <div class="book-list" id="book-list">
        <div class="empty"><div class="empty-icon">🔍</div><p>No books yet. Add your first one!</p></div>
      </div>
    </div>

  </div>
</div>

<script>
let allBooks = [];
let editingBno = null;

async function loadBooks() {
  const res = await fetch('/api/books');
  allBooks = await res.json();
  renderBooks(allBooks);
  updateStats(allBooks);
}

function updateStats(books) {
  document.getElementById('stat-count').textContent = books.length;
  const totalQty = books.reduce((s,b) => s + b.bqty, 0);
  const avgPrice = books.length ? Math.round(books.reduce((s,b) => s + b.bprice, 0) / books.length) : 0;
  document.getElementById('stat-qty').textContent = totalQty;
  document.getElementById('stat-price').textContent = '₹' + avgPrice;
}

function filterBooks(q) {
  q = q.toLowerCase();
  const filtered = allBooks.filter(b =>
    b.bname.toLowerCase().includes(q) || b.bauth.toLowerCase().includes(q)
  );
  renderBooks(filtered);
}

function renderBooks(books) {
  const el = document.getElementById('book-list');
  if (!books.length) {
    el.innerHTML = '<div class="empty"><div class="empty-icon">📭</div><p>No books found.</p></div>';
    return;
  }
  el.innerHTML = books.map(b => `
    <div class="book-item ${editingBno === b.bno ? 'selected' : ''}" onclick="selectBook(${b.bno})">
      <div class="book-avatar">${b.bname[0].toUpperCase()}</div>
      <div class="book-info">
        <div class="book-name">${b.bname}</div>
        <div class="book-author">${b.bauth}</div>
      </div>
      <div class="book-meta">
        <span class="badge">₹${b.bprice}</span>
        <span class="badge qty">×${b.bqty}</span>
        <button class="btn-icon danger" title="Delete" onclick="deleteBook(event,${b.bno})">🗑</button>
      </div>
    </div>
  `).join('');
}

function selectBook(bno) {
  const b = allBooks.find(x => x.bno === bno);
  if (!b) return;
  editingBno = bno;
  document.getElementById('f-bno').value   = b.bno;
  document.getElementById('f-bname').value = b.bname;
  document.getElementById('f-bauth').value = b.bauth;
  document.getElementById('f-bprice').value= b.bprice;
  document.getElementById('f-bqty').value  = b.bqty;
  document.getElementById('f-bno').disabled = true;
  document.getElementById('form-title').textContent = 'Edit Book';
  document.getElementById('submit-btn').textContent  = 'Save Changes';
  document.getElementById('edit-badge').style.display = '';
  document.getElementById('cancel-btn').style.display = '';
  renderBooks(allBooks);
}

function cancelEdit() {
  editingBno = null;
  clearForm();
  document.getElementById('f-bno').disabled = false;
  document.getElementById('form-title').textContent = 'Add Book';
  document.getElementById('submit-btn').textContent  = 'Add Book';
  document.getElementById('edit-badge').style.display = 'none';
  document.getElementById('cancel-btn').style.display = 'none';
  renderBooks(allBooks);
}

document.getElementById('cancel-btn').onclick = cancelEdit;

function clearForm() {
  ['f-bno','f-bname','f-bauth','f-bprice','f-bqty'].forEach(id => document.getElementById(id).value = '');
}

async function submitForm() {
  const bno    = parseInt(document.getElementById('f-bno').value);
  const bname  = document.getElementById('f-bname').value.trim();
  const bauth  = document.getElementById('f-bauth').value.trim();
  const bprice = parseInt(document.getElementById('f-bprice').value);
  const bqty   = parseInt(document.getElementById('f-bqty').value);

  if (!bno || !bname || !bauth || !bprice || !bqty) { toast('Please fill all fields.', 'error'); return; }

  if (editingBno) {
    await fetch(`/api/books/${editingBno}`, {
      method: 'PUT', headers: {'Content-Type':'application/json'},
      body: JSON.stringify({bname,bauth,bprice,bqty})
    });
    toast('Book updated!', 'success');
    cancelEdit();
  } else {
    const res = await fetch('/api/books', {
      method: 'POST', headers: {'Content-Type':'application/json'},
      body: JSON.stringify({bno,bname,bauth,bprice,bqty})
    });
    const data = await res.json();
    if (!data.ok) { toast(data.error, 'error'); return; }
    toast('Book added!', 'success');
    clearForm();
  }
  loadBooks();
}

async function deleteBook(e, bno) {
  e.stopPropagation();
  if (!confirm('Delete this book?')) return;
  await fetch(`/api/books/${bno}`, { method: 'DELETE' });
  if (editingBno === bno) cancelEdit();
  toast('Book deleted.', 'success');
  loadBooks();
}

function toast(msg, type='success') {
  const wrap = document.getElementById('toasts');
  const el = document.createElement('div');
  el.className = `toast ${type}`;
  el.textContent = msg;
  wrap.appendChild(el);
  setTimeout(() => el.remove(), 3000);
}

loadBooks();
</script>
</body>
</html>"""

@app.route("/")
def index():
    return render_template_string(HTML)

if __name__ == "__main__":
    init_db()
    print("\n  Library Manager running at  →  http://localhost:5000\n")
    app.run(debug=False)