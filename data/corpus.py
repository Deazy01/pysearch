"""
Demo corpus: 40 short tech articles used to demo and test pysearch.
Topics mirror Joshua's interests: embedded systems, Python, search engines, ML.

Each entry is (doc_id, title, text). The engine indexes title + text together.
"""

DOCS = [
    # ---------------- Embedded systems ----------------
    ("emb01", "Getting Started with the ESP32",
     "The ESP32 is a low-cost microcontroller with built-in WiFi and Bluetooth. "
     "It features a dual-core processor running at 240 MHz and plenty of GPIO pins. "
     "The ESP32 supports deep sleep modes that draw only microamps of current. "
     "Most developers program the ESP32 with the Arduino IDE or ESP-IDF."),

    ("emb02", "LoRaWAN for Long-Range IoT",
     "LoRaWAN is a wireless protocol built on LoRa, a long-range radio modulation technique. "
     "A single LoRaWAN gateway can cover several kilometers in open areas. "
     "LoRa devices can run for years on a small battery thanks to the efficient LoRa radio. "
     "LoRaWAN operates in unlicensed sub-gigahertz radio bands."),

    ("emb03", "Arduino vs ESP32: Which to Choose",
     "Arduino boards are famous for simplicity, while the ESP32 offers far more power. "
     "The ESP32 includes WiFi and Bluetooth that classic Arduino boards lack. "
     "Arduino sketches run on the ESP32 with only minor changes. "
     "Choose Arduino for simplicity and the ESP32 for connected projects."),

    ("emb04", "Introduction to FreeRTOS",
     "FreeRTOS is a real-time operating system for microcontrollers. "
     "It lets you run multiple tasks with different priorities on a single chip. "
     "FreeRTOS provides queues, semaphores, and mutexes for task synchronization. "
     "The ESP32 runs FreeRTOS underneath the Arduino framework."),

    ("emb05", "I2C Communication Protocol",
     "I2C is a two-wire serial protocol for connecting sensors to microcontrollers. "
     "It uses a clock line (SCL) and a data line (SDA) shared across devices. "
     "Each I2C device has a unique 7-bit address on the bus. "
     "I2C is ideal for short-distance sensor networks on a single board."),

    ("emb06", "SPI Communication Protocol",
     "SPI is a fast synchronous serial protocol using four wires. "
     "Unlike I2C, SPI uses separate chip-select lines for each device. "
     "SPI supports full-duplex communication at tens of megahertz. "
     "Displays and SD cards commonly connect over SPI."),

    ("emb07", "Bluetooth Low Energy (BLE) Basics",
     "Bluetooth Low Energy is designed for periodic small data transfers. "
     "BLE devices advertise their presence and exchange GATT characteristics. "
     "A BLE peripheral can run for months on a coin cell battery. "
     "The ESP32 supports both BLE and classic Bluetooth."),

    ("emb08", "MQTT Messaging for IoT",
     "MQTT is a lightweight publish-subscribe protocol for IoT devices. "
     "Devices publish messages to topics on a central MQTT broker. "
     "MQTT keeps connections open with minimal overhead and battery drain. "
     "Quality of service levels in MQTT guarantee message delivery."),

    ("emb09", "ESP32 Deep Sleep and Power Saving",
     "Deep sleep lets the ESP32 drop to about 10 microamps of current. "
     "In deep sleep the main CPUs power off and only the RTC domain stays alive. "
     "The ESP32 can wake from deep sleep on a timer or GPIO signal. "
     "Battery-powered ESP32 sensors spend 99 percent of their life in deep sleep."),

    ("emb10", "Embedded C Programming Tips",
     "Embedded C programming demands care with memory and timing. "
     "Avoid dynamic allocation on small microcontrollers with limited RAM. "
     "Use volatile for variables shared with interrupt handlers. "
     "Static analysis tools catch many embedded C bugs before flashing."),

    ("emb11", "MicroPython on the ESP32",
     "MicroPython brings Python to microcontrollers like the ESP32. "
     "You can control GPIO pins and read sensors with simple Python code. "
     "MicroPython on the ESP32 includes networking and asyncio support. "
     "It trades some speed for much faster prototyping than C."),

    ("emb12", "PCB Design Fundamentals",
     "Good PCB design starts with a clean schematic and thoughtful layout. "
     "Keep high-speed traces short and provide solid ground planes. "
     "Decoupling capacitors belong close to every chip's power pins. "
     "A two-layer PCB is enough for most hobby microcontroller projects."),

    # ---------------- Python ----------------
    ("py01", "Python for Beginners",
     "Python is a high-level language famous for readable syntax. "
     "Python runs on every major platform and has a huge standard library. "
     "Beginners love Python because working code takes few lines. "
     "Python is used for web apps, data science, automation, and more."),

    ("py02", "Python List Comprehensions",
     "List comprehensions build lists with a compact Python syntax. "
     "A Python list comprehension like [x*x for x in range(10)] replaces a loop. "
     "Python also supports dict and set comprehensions. "
     "Overusing comprehensions can hurt Python readability, so keep them simple."),

    ("py03", "Building Web Apps with Flask",
     "Flask is a lightweight Python web framework. "
     "A minimal Flask app needs only a few lines of Python code. "
     "Flask uses Jinja2 templates to render HTML pages. "
     "Many Python microservices are built with Flask."),

    ("py04", "Asyncio in Python",
     "Asyncio brings async and await syntax to Python. "
     "Python asyncio programs handle thousands of connections in one thread. "
     "Use Python asyncio for I/O-bound work like web scraping. "
     "CPU-bound Python code still needs multiprocessing, not asyncio."),

    ("py05", "Python Virtual Environments",
     "Virtual environments isolate Python dependencies per project. "
     "Create one with python -m venv and activate it before installing packages. "
     "Every Python project should have its own virtual environment. "
     "Virtual environments prevent version conflicts between Python projects."),

    ("py06", "Python Data Classes",
     "Data classes reduce boilerplate for simple Python classes. "
     "The @dataclass decorator auto-generates __init__ and __repr__. "
     "Python data classes work great for configuration objects. "
     "Use frozen data classes when you want immutable Python objects."),

    ("py07", "Debugging Python Programs",
     "The pdb debugger ships with every Python installation. "
     "Python tracebacks show the exact line where an error occurred. "
     "Add logging to Python programs instead of print statements. "
     "Type hints help Python linters catch bugs before runtime."),

    ("py08", "Packaging Python with pip",
     "pip installs Python packages from the PyPI registry. "
     "A requirements.txt file pins your Python dependencies. "
     "Publish your own Python package with a pyproject.toml file. "
     "pip and virtual environments together keep Python projects reproducible."),

    # ---------------- Search engines ----------------
    ("se01", "How Search Engines Work",
     "Search engines crawl the web and build an inverted index of terms. "
     "When you search, the engine looks up your terms in the inverted index. "
     "Ranking algorithms then order the matching pages by relevance. "
     "Modern search engines index billions of documents."),

    ("se02", "The Inverted Index Explained",
     "An inverted index maps each term to the documents containing it. "
     "Instead of scanning documents, the engine jumps straight to postings. "
     "The inverted index also stores term positions for phrase queries. "
     "Every serious search engine is built on an inverted index."),

    ("se03", "TF-IDF Ranking",
     "TF-IDF weights terms by frequency in a document and rarity in the collection. "
     "A high TF-IDF score means the term is important to that document. "
     "TF-IDF is simple but surprisingly effective for ranking. "
     "Many search engines started with TF-IDF before neural ranking."),

    ("se04", "The PageRank Algorithm",
     "PageRank ranks pages by the link graph of the web. "
     "A page linked by many important pages gets a high PageRank. "
     "PageRank made Google's early results far better than competitors. "
     "Modern engines combine PageRank-style signals with content ranking."),

    ("se05", "Phrase Search with Positions",
     "Phrase search finds documents where terms appear consecutively. "
     "The inverted index stores each term's positions to support phrase search. "
     "A phrase query checks that position(term2) equals position(term1) + 1. "
     "Phrase search is more precise than a bag-of-words query."),

    ("se06", "The Boolean Retrieval Model",
     "Boolean retrieval treats queries as AND, OR, and NOT expressions. "
     "Documents either match the boolean query or they do not. "
     "Boolean retrieval is precise but gives no ranking by itself. "
     "Lawyers and researchers still love boolean search operators."),

    ("se07", "Web Crawling Basics",
     "A crawler fetches pages and extracts links to discover more pages. "
     "Polite crawlers respect robots.txt and rate limits. "
     "The crawl frontier prioritizes which URLs to fetch next. "
     "Search engines crawl trillions of URLs continuously."),

    ("se08", "Tokenization and Stemming",
     "Tokenization splits text into terms for the inverted index. "
     "Stemming reduces running and runs to the root run. "
     "Stopword removal drops common words like the and is. "
     "Good tokenization directly improves search quality."),

    # ---------------- Machine learning ----------------
    ("ml01", "Random Forests Explained",
     "A random forest is an ensemble of many decision trees. "
     "Each tree in a random forest trains on a random subset of data. "
     "Random forests handle nonlinear patterns without much tuning. "
     "The random forest remains a strong baseline for tabular data."),

    ("ml02", "Introduction to Neural Networks",
     "Neural networks stack layers of simple nonlinear units. "
     "Training a neural network adjusts weights with gradient descent. "
     "Deep neural networks power modern image and language models. "
     "Neural networks need lots of data to generalize well."),

    ("ml03", "Overfitting and Cross-Validation",
     "Overfitting happens when a model memorizes training noise. "
     "Cross-validation estimates how a model performs on unseen data. "
     "K-fold cross-validation splits data into k rotating test sets. "
     "Simpler models often beat complex ones once cross-validation is honest."),

    ("ml04", "TF-IDF for Text Classification",
     "TF-IDF turns documents into numeric vectors for classifiers. "
     "A logistic regression on TF-IDF features is a classic text baseline. "
     "TF-IDF features capture which words distinguish each class. "
     "Even in the deep learning era, TF-IDF baselines are worth running."),

    ("ml05", "Gradient Descent",
     "Gradient descent minimizes a loss by stepping against the gradient. "
     "The learning rate controls each gradient descent step size. "
     "Stochastic gradient descent uses mini-batches for speed. "
     "Almost every neural network trains with gradient descent."),

    ("ml06", "Decision Trees",
     "Decision trees split data on the most informative features. "
     "A single decision tree is easy to interpret but overfits quickly. "
     "Pruning keeps decision trees from growing too deep. "
     "Random forests fix decision trees by averaging many of them."),

    # ---------------- General CS ----------------
    ("cs01", "Git Version Control",
     "Git tracks changes to code across branches and history. "
     "Commit early and often to keep your Git history useful. "
     "Git branching lets teams work in parallel safely. "
     "Push your Git commits to GitHub for backup and collaboration."),

    ("cs02", "Docker Containers",
     "Docker packages apps with their dependencies into containers. "
     "A Dockerfile describes how to build a Docker image. "
     "Docker containers start in milliseconds and run anywhere. "
     "Use Docker Compose to orchestrate multi-container setups."),

    ("cs03", "REST API Design",
     "REST APIs use HTTP verbs like GET, POST, and DELETE. "
     "Good REST design uses nouns for resources and proper status codes. "
     "Version your REST API so clients don't break on changes. "
     "Document every REST endpoint with examples."),

    ("cs04", "Big-O Notation",
     "Big-O describes how runtime grows with input size. "
     "Binary search is O(log n) while linear search is O(n). "
     "An O(n^2) algorithm can be 10,000x slower than O(n log n). "
     "Always consider Big-O before optimizing code."),

    ("cs05", "TCP vs UDP",
     "TCP guarantees ordered, reliable delivery of data. "
     "UDP is faster but may drop or reorder packets. "
     "Video calls often use UDP while file transfers need TCP. "
     "Choose TCP for correctness and UDP for low latency."),

    ("cs06", "Linux Command Line",
     "The Linux terminal rewards those who learn its core tools. "
     "grep, sed, and awk process text streams on Linux. "
     "Pipe Linux commands together to build powerful one-liners. "
     "Every developer should be comfortable on the Linux command line."),
]


def load_corpus():
    """Return [(doc_id, full_text)] with title prepended for better matching."""
    return [(doc_id, f"{title}. {text}") for doc_id, title, text in DOCS]
