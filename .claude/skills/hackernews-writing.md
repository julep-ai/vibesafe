# HackerNews Writing Skill

Expert skill for crafting technical content, documentation, blog posts, and titles that resonate with the Hacker News audience and generate meaningful engagement.

## Overview

Hacker News (YC's news aggregator) has a unique, technically sophisticated audience with specific expectations for content quality, depth, and presentation. This skill encodes patterns from top-performing HN submissions to help create content that generates discussion, upvotes, and lasting value.

**Core Philosophy:** HN readers value substance over style, depth over breadth, honesty over hype, and technical rigor over marketing speak.

## Understanding the HN Audience

### Demographics & Preferences

**Who reads HN:**
- Software engineers, CTOs, technical founders
- Systems programmers, infrastructure engineers
- Computer science researchers and academics
- Engineering managers and technical leaders
- Startup founders and indie hackers
- Open source maintainers and contributors

**What they value:**
- Technical depth and first-hand experience
- Novel insights or non-obvious solutions
- Production war stories and hard-won lessons
- Clear explanations of complex topics
- Data-driven analysis and benchmarks
- Honest assessments of trade-offs
- Historical context and evolution of ideas
- Creative problem-solving approaches

**What they reject:**
- Marketing content disguised as technical writing
- Clickbait titles or sensationalism
- Surface-level tutorials without depth
- Hype without substance
- Unsupported claims or hand-waving
- Content that wastes their time
- Obvious or widely-known information
- Self-promotion without genuine value

### Content Tiers on HN

**🔥 Front Page (500+ points):**
- Deep technical investigations
- Novel algorithms or approaches
- Production outage postmortems
- Significant performance breakthroughs
- Paradigm-shifting ideas
- Well-researched historical pieces

**📈 Rising (50-200 points):**
- Solid technical tutorials
- Tool comparisons with benchmarks
- Experience reports from production
- Debugging mysteries solved
- Lesser-known techniques
- Good technical questions

**💬 Discussion Generators (any points, 50+ comments):**
- Controversial technical opinions
- Language/framework comparisons
- Architecture decisions and trade-offs
- "X considered harmful" critiques
- Questions about best practices

## Writing Titles That Work on HN

### The Golden Rules

**✅ DO:**
1. **Be direct and factual** - State exactly what the content is
2. **Use specific technical terms** - Not "database" but "PostgreSQL 16"
3. **Include concrete numbers** - "10x faster" with benchmark data to back it up
4. **State the problem clearly** - "Why X fails at scale"
5. **Ask genuine questions** - "How does SQLite handle concurrent writes?"
6. **Use version numbers** - "Python 3.13's new JIT compiler"
7. **Be honest about scope** - "A minimal guide to..." not "The complete guide to..."

**❌ DON'T:**
1. **Use clickbait** - "You won't believe...", "This one trick..."
2. **Add superlatives without proof** - "The best", "The ultimate"
3. **Make it about yourself** - "How I..." unless genuinely novel
4. **Use marketing speak** - "Revolutionary", "Game-changing", "Disruptive"
5. **Ask rhetorical questions** - "Is X the future?" (unless genuinely exploring)
6. **Use ALL CAPS or excessive punctuation** - "AMAZING!!!"
7. **Be vague** - "Some thoughts on databases" vs "PostgreSQL vs MySQL for time-series data"

### Title Patterns That Work

#### Pattern 1: Direct Technical Description
```
✅ "Implementing a B-tree in Rust with concurrent access"
✅ "How Git stores objects: a deep dive into pack files"
✅ "Building a CPU profiler from scratch in C"
✅ "SQLite's query planner explained with examples"
```

Why it works: Clear, specific, promises technical depth

#### Pattern 2: Problem → Solution
```
✅ "Debugging a 50ms latency spike in production PostgreSQL"
✅ "Reducing Docker image size from 1GB to 100MB"
✅ "Fixing a memory leak in a 10-year-old Python codebase"
✅ "Solving the N+1 query problem in GraphQL"
```

Why it works: Concrete problem, measurable outcome, relatable struggle

#### Pattern 3: Comparative Analysis
```
✅ "Benchmarking serialization: JSON vs MessagePack vs Protocol Buffers"
✅ "Kubernetes vs Nomad: 2 years in production"
✅ "SQLite vs PostgreSQL: When to use which"
✅ "LLVM vs GCC: Compilation speed and binary size"
```

Why it works: Data-driven, helps decision-making, balanced perspective

#### Pattern 4: Technical Investigation
```
✅ "What happens when you type 'ls' and press Enter?"
✅ "How does Redis persist data without blocking writes?"
✅ "Why is Python's 'dict' so fast?"
✅ "Exploring the Linux kernel's scheduler"
```

Why it works: Satisfies curiosity, educational, peels back abstractions

#### Pattern 5: Production War Stories
```
✅ "Postmortem: How we lost $100k to a race condition"
✅ "The bug that took 3 months to find: a SIGSEGV story"
✅ "When your database runs out of transaction IDs"
✅ "How a single line of code brought down our infrastructure"
```

Why it works: Hard-won lessons, humility, preventable disasters

#### Pattern 6: Unconventional Approaches
```
✅ "Building a web server in pure Bash"
✅ "Using SQLite as an application file format"
✅ "Implementing malloc() in 100 lines of C"
✅ "Writing a compiler in spreadsheet formulas"
```

Why it works: Creative, educational, demonstrates deep understanding

#### Pattern 7: Historical/Contextual
```
✅ "The rise and fall of CORBA"
✅ "How Unix pipelines work: The 1973 implementation"
✅ "Why the Linux kernel uses goto"
✅ "The history of NaN in floating point"
```

Why it works: Context enriches understanding, connects past to present

#### Pattern 8: Performance Deep Dives
```
✅ "Making Python code 100x faster with Cython"
✅ "How we reduced API latency from 500ms to 20ms"
✅ "Why our Rust service uses 10x less memory than Java"
✅ "Optimizing PostgreSQL for 1M writes/second"
```

Why it works: Concrete numbers, technical details, actionable insights

### Title Anti-Patterns (What to Avoid)

❌ **The Humble Brag:**
```
"How I built a startup to $1M ARR in 6 months"
"My side project hit #1 on HN"
```
Better: Focus on the technical achievement, not personal success

❌ **The Vague Teaser:**
```
"Some interesting thoughts on scalability"
"A few notes about Kubernetes"
```
Better: Be specific about what insights you're sharing

❌ **The Obvious Tutorial:**
```
"Introduction to Python basics"
"Getting started with Git"
```
Better: Find a non-obvious angle or advanced technique

❌ **The Marketing Pitch:**
```
"Why [Our Product] is the future of databases"
"Announcing [Startup]: Revolutionizing DevOps"
```
Better: Focus on technical innovation, not business proposition

❌ **The Inflammatory Clickbait:**
```
"Why [Popular Technology] is terrible and you should stop using it"
"Everyone is doing [X] wrong"
```
Better: Thoughtful critique with nuance and alternatives

### Title Length Guidelines

**Ideal range:** 50-80 characters (8-12 words)
- Short enough to scan quickly
- Long enough to be specific
- Fits on one line in HN interface

**Examples:**
```
✅ "Understanding PostgreSQL's MVCC implementation" (48 chars) ✅
✅ "How I debugged a memory leak in production Kubernetes" (62 chars) ✅
✅ "Building a lock-free queue in C with atomic operations" (55 chars) ✅

❌ "Databases" (9 chars) - Too vague ❌
❌ "A comprehensive deep-dive investigation into the intricate details of how modern relational database management systems implement multi-version concurrency control mechanisms" (175 chars) - Too long ❌
```

## Writing Content That Resonates

### Structure for Success

#### 1. The Opening (First 2-3 Paragraphs)

**Hook immediately with the core insight:**

✅ **Good Opening:**
```markdown
Last Tuesday, our API started responding in 3 seconds instead of 50ms.
Every request to /users/:id was timing out. The weird part? Nothing had
changed in the code. After 6 hours of debugging, we found the culprit:
a database query that had worked fine for 2 years suddenly hit a performance
cliff when we crossed 1 million users.

Here's what we learned about PostgreSQL's query planner and how to prevent
this from happening to you.
```

Why it works: Immediate problem, stakes, mystery, promise of solution

❌ **Bad Opening:**
```markdown
In today's fast-paced world of web development, performance is increasingly
becoming a critical concern for engineering teams. As applications scale to
meet the demands of millions of users, database optimization becomes essential.
This blog post will explore some of the strategies we've discovered...
```

Why it fails: Generic, slow burn, no hook, marketing speak

**Elements of a strong opening:**
1. **State the problem immediately** - No preamble
2. **Include a hook** - Something unexpected or surprising
3. **Promise specific value** - What will the reader learn?
4. **Be concrete** - Real numbers, real systems, real problems
5. **Skip the introduction** - Jump right into the meat

#### 2. The Technical Deep Dive (Main Content)

**Core Principles:**

**A. Show Your Work**
```markdown
❌ "We optimized the query and it got faster."

✅ "Here's the original query:
```sql
SELECT * FROM users
WHERE created_at > '2024-01-01'
ORDER BY id;
```

The EXPLAIN ANALYZE showed a sequential scan:
```
Seq Scan on users  (cost=0.00..35234.00 rows=1000000 width=128)
  Filter: (created_at > '2024-01-01'::date)
```

After adding an index on (created_at, id):
```sql
CREATE INDEX idx_users_created_at_id ON users(created_at, id);
```

The same query now uses the index:
```
Index Scan using idx_users_created_at_id  (cost=0.42..8234.00 rows=250000 width=128)
```

Query time dropped from 2.3s to 45ms."
```

**B. Include Code Examples**
- Show real code, not pseudocode
- Include error messages and outputs
- Demonstrate before/after comparisons
- Comment non-obvious parts
- Keep examples minimal but complete

**C. Add Benchmarks and Data**
```markdown
✅ Good benchmark section:

## Performance Comparison

Test setup:
- Machine: AWS c5.xlarge (4 vCPU, 8GB RAM)
- Dataset: 1M records, 10KB average size
- Runs: 100 iterations, median reported

| Approach | Throughput (req/s) | p50 latency | p99 latency | Memory |
|----------|-------------------|-------------|-------------|--------|
| Baseline | 1,200 | 42ms | 150ms | 2.1GB |
| Option A | 3,400 | 15ms | 45ms | 1.8GB |
| Option B | 5,100 | 8ms | 28ms | 3.2GB |

Option B wins on speed but uses 50% more memory. For our use case
(memory-constrained containers), we chose Option A.
```

**D. Explain the "Why" Not Just the "How"**
```markdown
❌ "Use connection pooling with 20 connections."

✅ "We set the connection pool to 20 connections because:
1. Our app runs 4 processes × 5 threads = 20 concurrent handlers
2. PostgreSQL's max_connections is 100
3. We run 4 app instances, so 20 × 4 = 80 connections (within limit)
4. Benchmarking showed diminishing returns above 20 per instance
5. This leaves 20 connections for admin tasks and monitoring

Connection pool configuration:
```python
pool_size=20,
max_overflow=0,  # No overflow - fail fast instead
pool_timeout=30,
pool_recycle=3600
```
"
```

**E. Acknowledge Trade-offs and Limitations**
```markdown
✅ Good trade-off discussion:

## Why We Chose Rust Over Go

Pros:
- 40% lower memory usage in our benchmarks
- Better CPU utilization (no GC pauses)
- Type system caught entire classes of bugs
- Zero-cost abstractions matched C++ performance

Cons:
- 3x longer development time initially
- Steep learning curve for the team
- Longer compile times (5 minutes vs 30 seconds for Go)
- Smaller ecosystem for some use cases
- Harder to hire for

We chose Rust because our bottleneck was resource cost (running thousands
of instances), not development velocity. If we were an early-stage startup
iterating quickly, Go would've been the better choice.
```

**F. Include Failure Stories**
```markdown
✅ "We tried three approaches before this one worked:

1. **Redis caching** - Cache hit rate was only 30% due to data distribution
2. **Read replicas** - Replication lag caused stale data issues
3. **Materialized views** - Refresh took 10 minutes, blocking writes

Finally, we implemented partitioning by customer_id and query performance
improved 50x."
```

#### 3. Code Style in Content

**Make code readable and production-quality:**

✅ **Good code example:**
```python
import asyncio
from typing import List, Optional
import httpx

class APIClient:
    """HTTP client with retry logic and connection pooling."""

    def __init__(self, base_url: str, timeout: int = 30):
        self.base_url = base_url
        self.client = httpx.AsyncClient(
            timeout=timeout,
            limits=httpx.Limits(max_connections=100)
        )

    async def fetch_user(self, user_id: int) -> Optional[dict]:
        """Fetch user by ID with exponential backoff retry.

        Returns None if user not found, raises exception on other errors.
        """
        for attempt in range(3):
            try:
                response = await self.client.get(
                    f"{self.base_url}/users/{user_id}"
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 404:
                    return None
                if attempt == 2:  # Last attempt
                    raise
                await asyncio.sleep(2 ** attempt)  # Exponential backoff

        return None

# Usage
client = APIClient("https://api.example.com")
user = await client.fetch_user(123)
```

Why it works:
- Type hints included
- Docstrings explain behavior
- Error handling is explicit
- Comments explain non-obvious logic
- Real-world pattern (retry with backoff)
- Complete and runnable

❌ **Bad code example:**
```python
def get_user(id):
    # Get the user
    r = requests.get(url + "/users/" + str(id))
    return r.json()
```

Why it fails:
- No error handling
- No type hints
- Unclear what happens on failure
- Not production-ready

#### 4. The Conclusion

**End with actionable takeaways:**

✅ **Good conclusion:**
```markdown
## Key Takeaways

1. **Profile before optimizing** - We wasted 2 weeks on the wrong bottleneck
2. **Index cardinality matters** - Indexes on low-cardinality columns hurt performance
3. **Connection pools need tuning** - Default settings rarely work at scale
4. **Monitor query plans** - They can change as data grows

If you're seeing slow PostgreSQL queries:
1. Run EXPLAIN ANALYZE on your slowest queries
2. Check pg_stat_statements for query patterns
3. Look for sequential scans on large tables
4. Verify index usage with pg_stat_user_indexes

Full benchmarking code: https://github.com/example/pg-optimization
Discussion: https://news.ycombinator.com/item?id=XXXXX
```

**Elements of a strong conclusion:**
- Numbered takeaways (3-5 points)
- Actionable next steps
- Links to code/further reading
- Invitation for discussion
- No sales pitch or marketing

❌ **Bad conclusion:**
```markdown
## Conclusion

In conclusion, database optimization is a complex topic with many facets
to consider. We hope this post has been helpful and informative. If you
enjoyed this content, please subscribe to our newsletter for more tips
and tricks. Check out our product at [startup.com] for automated database
optimization!
```

### Writing Style Guide

#### Tone and Voice

**✅ DO:**
- Write in first person ("we did", "I found") for experience reports
- Use second person ("you can", "you should") for tutorials
- Be conversational but precise
- Show humility about mistakes
- Express genuine enthusiasm for technical topics
- Use humor sparingly and naturally

**❌ DON'T:**
- Use corporate/marketing voice
- Be condescending or assume ignorance
- Over-explain obvious concepts
- Use excessive jargon without definitions
- Write in passive voice
- Add fluff or filler content

#### Sentence Structure

**✅ Good sentences:**
```markdown
The bug appeared at 3am on a Saturday. Classic.

PostgreSQL's MVCC implementation is elegant: each row version has a
transaction ID. When you read a row, you see the version that was
committed before your transaction started. This makes reads non-blocking.

We benchmarked three approaches. Rust was fastest but had the longest
compile times. Go was middle-ground. Python was slowest but easiest to modify.
```

Why it works: Short, direct, varied length, no wasted words

**❌ Bad sentences:**
```markdown
In the context of modern database systems, it is often the case that
various concurrency control mechanisms are employed in order to ensure
that multiple transactions can be processed simultaneously without
interfering with each other's operations.
```

Why it fails: Verbose, passive voice, academically bloated

#### Paragraph Structure

**Ideal paragraph:**
- 2-5 sentences
- One main idea per paragraph
- Start with topic sentence
- End with transition or insight

**Break up long content with:**
- Subheadings every 2-3 paragraphs
- Code blocks and examples
- Lists and tables
- Quotes and callouts
- Diagrams and charts

#### Technical Terminology

**Use precise technical terms:**
```markdown
✅ "PostgreSQL uses MVCC (Multi-Version Concurrency Control)"
✅ "The algorithm is O(n log n) in the average case"
✅ "We hit the L1 cache 95% of the time"
✅ "The race condition occurs during the compare-and-swap"
```

**Define acronyms on first use:**
```markdown
✅ "We implemented CRDT (Conflict-free Replicated Data Types) for
distributed state management."

❌ "We used CRDTs." (first mention, no definition)
```

**Avoid buzzwords:**
```markdown
❌ "We leverage AI-powered cloud-native microservices"
✅ "We use GPT-4 to classify messages in our Kubernetes cluster"
```

### Content Types That Work

#### Type 1: The Technical Deep Dive

**Purpose:** Explain how something works at a deep level

**Structure:**
1. What is X?
2. Why does X matter?
3. How does X work internally?
4. Common pitfalls and gotchas
5. Real-world usage examples
6. Performance characteristics
7. Alternative approaches

**Example topics:**
- "How Linux load balancers work: A deep dive into IPVS"
- "Understanding JWT: Security considerations and implementation"
- "Inside V8's optimizing compiler"

#### Type 2: The Production Postmortem

**Purpose:** Share hard-won lessons from production incidents

**Structure:**
1. The incident (what went wrong)
2. Impact and timeline
3. Debugging process (dead ends included)
4. Root cause analysis
5. The fix
6. Prevention measures
7. What we learned

**Example topics:**
- "Postmortem: The day we lost 100k database rows"
- "How a single character typo took down our production cluster"
- "Debugging a 1-second delay in Kubernetes DNS lookups"

#### Type 3: The Benchmark Comparison

**Purpose:** Compare tools/approaches with data

**Structure:**
1. What we're comparing and why
2. Test methodology
3. Environment and setup
4. Benchmark results (tables/graphs)
5. Analysis and interpretation
6. Trade-offs discussion
7. Recommendations by use case

**Example topics:**
- "Benchmarking message queues: Kafka vs RabbitMQ vs NATS"
- "Container runtimes compared: Docker vs Podman vs containerd"
- "Python web frameworks: FastAPI vs Flask vs Django performance"

#### Type 4: The "Show HN" Project

**Purpose:** Share something you built, focusing on technical interesting bits

**Structure:**
1. What it is (1 sentence)
2. Why you built it (problem/motivation)
3. Technical highlights (the interesting parts)
4. Architecture/design decisions
5. Challenges and solutions
6. Demo/examples
7. Links (GitHub, live demo)

**Example topics:**
- "Show HN: I built a SQLite clone in Rust to understand databases"
- "Show HN: A text editor in 1000 lines of C"
- "Show HN: Self-hosted alternative to Vercel using Kubernetes"

#### Type 5: The Debugging Mystery

**Purpose:** Tell the story of solving a hard bug

**Structure:**
1. The symptoms (mysterious behavior)
2. Initial hypotheses
3. Dead ends and false leads
4. The breakthrough moment
5. The root cause
6. The fix
7. Lessons learned

**Example topics:**
- "The bug that only appeared on Tuesdays"
- "Debugging a heisenbug in multi-threaded Rust"
- "How I tracked down a memory corruption bug using gdb"

#### Type 6: The Experience Report

**Purpose:** Share what you learned from using X in production

**Structure:**
1. What we built and why we chose X
2. Initial experience and setup
3. What worked well
4. Pain points and gotchas
5. Performance in production
6. Would we choose it again?
7. Advice for others

**Example topics:**
- "One year of using Elixir in production"
- "Migrating from MongoDB to PostgreSQL: What we learned"
- "Running Nomad instead of Kubernetes: 6 months in"

#### Type 7: The Performance Optimization

**Purpose:** Document significant performance improvements

**Structure:**
1. The performance problem
2. Baseline measurements
3. Profiling and investigation
4. Optimization attempts (successes and failures)
5. Final solution and results
6. Before/after comparisons
7. Generalizable lessons

**Example topics:**
- "Reducing Docker build time from 30 minutes to 40 seconds"
- "How we made our Python API 50x faster"
- "Optimizing PostgreSQL: From 100 to 10,000 queries/second"

### Visual Elements

#### Code Blocks

**Always include:**
- Syntax highlighting (specify language)
- Comments for non-obvious parts
- Complete, runnable examples when possible
- Input and output examples

```markdown
✅ Good code block:

```python
# Binary search implementation with bounds checking
def binary_search(arr: List[int], target: int) -> int:
    """Return index of target in sorted arr, or -1 if not found."""
    left, right = 0, len(arr) - 1

    while left <= right:
        mid = left + (right - left) // 2  # Avoid overflow

        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            left = mid + 1
        else:
            right = mid - 1

    return -1

# Example usage:
numbers = [1, 3, 5, 7, 9, 11, 13, 15]
index = binary_search(numbers, 7)  # Returns 3
```
```

#### Tables

**Use tables for:**
- Benchmark results
- Feature comparisons
- Performance metrics
- Before/after data

```markdown
| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| Response time (p50) | 234ms | 45ms | 80% |
| Response time (p99) | 1.2s | 120ms | 90% |
| Throughput | 450 req/s | 2100 req/s | 4.6x |
| Memory usage | 3.2GB | 1.8GB | 44% |
| CPU utilization | 85% | 42% | 51% |
```

#### Diagrams and Charts

**Include diagrams for:**
- Architecture overviews
- Data flow
- State machines
- Network topology
- Algorithm visualization

**Tools that work well:**
- ASCII diagrams (plain text, always renders)
- Mermaid (supported on GitHub)
- Simple PNG/SVG (keep it clean)
- Excalidraw (hand-drawn style, approachable)

**Example ASCII diagram:**
```
┌─────────────┐
│   Client    │
└──────┬──────┘
       │ HTTP
       ▼
┌─────────────┐     ┌──────────┐
│  API Server │────▶│  Redis   │
└──────┬──────┘     └──────────┘
       │
       │ SQL
       ▼
┌─────────────┐
│ PostgreSQL  │
└─────────────┘
```

#### Callout Boxes

**Use for important notes:**

```markdown
> ⚠️ **Warning**: This approach has a race condition when multiple
> processes access the same file. Use file locking with `fcntl.flock()`
> or switch to a database for multi-process deployments.

> 💡 **Tip**: PostgreSQL's `EXPLAIN (ANALYZE, BUFFERS)` shows cache hits
> and disk reads. Look for "Buffers: shared hit" vs "shared read".

> 🔍 **Debug**: Enable query logging with `log_min_duration_statement = 0`
> in postgresql.conf. Remember to disable it after debugging!
```

## Topic Selection Strategy

### High-Potential Topics

**✅ Topics that consistently do well:**

1. **Performance optimization stories**
   - "Reducing latency from X to Y"
   - "How we cut costs by 80% with optimization Z"
   - "Making X 100x faster"

2. **Database deep dives**
   - PostgreSQL internals
   - SQLite usage patterns
   - Database query optimization
   - Replication and consistency

3. **Systems programming**
   - Operating system internals
   - Network programming
   - Memory management
   - Concurrency and parallelism

4. **Production war stories**
   - Outage postmortems
   - Debugging mysteries
   - Scale challenges
   - Hard-won lessons

5. **Language internals**
   - How interpreters work
   - Compiler optimizations
   - Memory models
   - Type systems

6. **Infrastructure topics**
   - Kubernetes internals
   - Container runtime details
   - CI/CD optimization
   - Monitoring and observability

7. **Security research**
   - Vulnerability discoveries
   - Exploit development (ethical)
   - Security audit findings
   - Cryptography implementations

8. **Historical retrospectives**
   - Evolution of technologies
   - "Where are they now" for old tech
   - Design decisions and their consequences
   - Lost knowledge and forgotten techniques

### Evergreen vs Trendy

**Evergreen content (long-lasting value):**
- Fundamental concepts (algorithms, data structures)
- Core technologies (TCP/IP, HTTP, SQL)
- Timeless patterns (design patterns, architectures)
- Problem-solving approaches
- Performance optimization techniques

**Trendy content (timely value):**
- New language/framework releases
- Breaking security vulnerabilities
- Industry incidents (major outages)
- Emerging technologies
- Current debates (Rust vs Go, etc.)

**Balance:** Mix evergreen depth with timely relevance

### Finding Your Angle

**Ask yourself:**
1. What's the non-obvious insight here?
2. What would have saved me weeks if I'd known it earlier?
3. What surprised me about this?
4. What do the docs not tell you?
5. What's the hidden complexity?
6. What did I learn the hard way?

**Example transformations:**
```
Generic: "Introduction to Redis"
✅ Better: "Using Redis as a primary database: What works and what doesn't"

Generic: "Understanding Docker"
✅ Better: "How Docker actually works: Namespaces, cgroups, and union filesystems"

Generic: "Guide to GraphQL"
✅ Better: "GraphQL at scale: Solving the N+1 problem, caching, and security"
```

## Common Mistakes to Avoid

### Content Mistakes

❌ **1. Burying the lede**
```markdown
Bad: [3 paragraphs about context]
     [2 paragraphs about your background]
     [Finally, the actual insight]

Good: [Immediate insight]
      [Context as needed]
      [Background only if relevant]
```

❌ **2. No code examples**
```markdown
Bad: "We optimized the algorithm and it got faster."

Good: [Show the slow code]
      [Show the fast code]
      [Show benchmark results]
```

❌ **3. Marketing speak**
```markdown
Bad: "Our revolutionary AI-powered solution leverages machine learning"

Good: "We use a Random Forest classifier trained on 10k examples"
```

❌ **4. Unsupported claims**
```markdown
Bad: "This is the fastest JSON parser ever written."

Good: "This parser handles 2.5GB/s on our benchmark (M1 Max, 10 cores),
      compared to simdjson's 2.1GB/s and RapidJSON's 1.8GB/s."
```

❌ **5. Incomplete examples**
```markdown
Bad:
```python
result = process_data(data)
```

Good:
```python
import pandas as pd
from typing import DataFrame

def process_data(df: DataFrame) -> DataFrame:
    """Remove duplicates and normalize values."""
    df = df.drop_duplicates(subset=['id'])
    df['value'] = (df['value'] - df['value'].mean()) / df['value'].std()
    return df

# Example usage:
data = pd.DataFrame({
    'id': [1, 2, 2, 3],
    'value': [10, 20, 20, 30]
})
result = process_data(data)
# Result: 3 rows with normalized values
```
```

❌ **6. No trade-off discussion**
```markdown
Bad: "We switched to microservices and everything is better."

Good: "Microservices gave us better scalability (10x throughput) but
      increased complexity (3x more repos, more network calls, harder
      debugging). Worth it for us at our scale, but I'd use a monolith
      for a small team."
```

### Title Mistakes

❌ **1. The vague title**
```
"Some thoughts on databases"
Better: "PostgreSQL vs MySQL for time-series data: A benchmark study"
```

❌ **2. The clickbait title**
```
"This one weird trick will make your code 10x faster!"
Better: "Reducing Python startup time with module-level imports"
```

❌ **3. The me-focused title**
```
"How I became a 10x developer"
Better: "5 debugging techniques that saved me 100 hours"
```

❌ **4. The generic tutorial**
```
"Getting started with Docker"
Better: "Docker internals: How containers actually work"
```

❌ **5. The vendor title**
```
"Why you should use [Our Product]"
Better: "Building a distributed cache with Redis: Patterns and pitfalls"
```

## Checklist for HN-Ready Content

### Before Publishing

**Content Quality:**
- [ ] Title is specific, factual, and under 80 characters
- [ ] Opening paragraph hooks immediately (no preamble)
- [ ] Technical depth is substantial (not surface-level)
- [ ] Code examples are complete and runnable
- [ ] Benchmarks include methodology and environment
- [ ] Trade-offs and limitations are discussed
- [ ] Failures and dead ends are included
- [ ] Claims are supported with evidence
- [ ] Conclusion has actionable takeaways
- [ ] No marketing speak or hype

**Technical Accuracy:**
- [ ] Code has been tested
- [ ] Benchmarks have been verified
- [ ] Technical terms are used correctly
- [ ] Version numbers are current
- [ ] Links work and are relevant
- [ ] Examples are reproducible

**Readability:**
- [ ] Paragraphs are short (2-5 sentences)
- [ ] Subheadings break up long sections
- [ ] Code blocks have syntax highlighting
- [ ] Tables and diagrams enhance clarity
- [ ] Sentences are direct and clear
- [ ] Technical jargon is defined

**Value Proposition:**
- [ ] Reader will learn something new
- [ ] Content has practical applications
- [ ] Insights are non-obvious
- [ ] Problems discussed are relatable
- [ ] Solutions are generalizable

### Submission Strategy

**Timing:**
- Best times: 8-10am EST on weekdays
- Avoid: Late Friday, weekends, holidays
- Competition: Check /newest before posting

**Format:**
- For blog posts: Submit URL directly
- For GitHub: Submit to README or docs
- For text posts: Use "Text" submission type
- Include "Show HN:" prefix for your projects

**Engagement:**
- Monitor early comments (first 30 minutes critical)
- Respond thoughtfully to questions
- Acknowledge criticisms gracefully
- Add clarifications if needed
- Don't argue or defend aggressively

## Example: Rewriting Content for HN

### Before: Generic Tutorial

**Title:** "Introduction to PostgreSQL Performance"

**Opening:**
```markdown
PostgreSQL is one of the most popular open-source relational databases
in use today. As applications grow and scale, performance becomes
increasingly important. In this tutorial, we'll explore some basic
concepts around PostgreSQL performance optimization.

There are many factors that contribute to database performance...
```

**Problems:**
- Generic title
- Slow, fluffy opening
- No specific value proposition
- No hook or curiosity

### After: HN-Optimized

**Title:** "Why PostgreSQL's query planner chose a slow sequential scan: A debugging story"

**Opening:**
```markdown
Our dashboard query went from 50ms to 8 seconds overnight. Nothing changed
in the code. The EXPLAIN output showed PostgreSQL chose a sequential scan
over our carefully-crafted index on a 50M row table.

After digging through pg_stats and experimenting with query costs, I found
the culprit: our nightly ANALYZE job stopped running 2 weeks ago. The planner
was using stale statistics from when the table had 2M rows.

Here's what I learned about how PostgreSQL's cost-based optimizer makes
decisions, and how to debug when it chooses poorly.
```

**Improvements:**
- Specific, intriguing title
- Immediate problem statement
- Real numbers and stakes
- Mystery element
- Promise of practical insights

**Body would include:**
```markdown
## Understanding query planner statistics

PostgreSQL's planner uses statistics from pg_stats to estimate:
- Row count in each table
- Cardinality of column values
- Correlation of physical and logical ordering

When statistics are stale, estimates are wrong, and the planner chooses
suboptimal plans.

## Debugging the issue

1. Check when statistics were last updated:
```sql
SELECT schemaname, tablename, last_analyze, last_autoanalyze
FROM pg_stat_user_tables
WHERE tablename = 'dashboard_events';
```

Result showed last analyze was 14 days ago.

2. Check the planner's estimates vs reality:
```sql
EXPLAIN (ANALYZE, BUFFERS)
SELECT * FROM dashboard_events
WHERE user_id = 12345;
```

Output:
```
Seq Scan on dashboard_events
  (cost=0.00..854234.00 rows=50000000 width=128)
  (actual rows=12 loops=1)
```

Estimated 50M rows, actually found 12 rows. No wonder it chose a seq scan.

[Continue with solution, prevention, lessons...]
```

## Templates and Formulas

### The Performance Optimization Template

```markdown
# [Specific Task]: From [Slow Metric] to [Fast Metric]

Last [timeframe], our [system] started [symptom]. [Concrete impact statement].

## The Problem

[Detailed problem description with measurements]

## Investigation

1. Initial profiling with [tool]:
```
[profiler output]
```

2. Hypothesis: [what we thought was wrong]

3. Testing: [what we tried]

4. Results: [what happened - including failures]

## The Solution

[Describe winning approach]

```[language]
[code example]
```

## Results

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| [Key metric] | [value] | [value] | [%/x] |

## Lessons Learned

1. [Insight 1]
2. [Insight 2]
3. [Insight 3]

## Resources

- Code: [github link]
- Benchmarks: [link]
```

### The Comparison Template

```markdown
# [Tool A] vs [Tool B] vs [Tool C]: [Specific Use Case]

We needed [specific requirement] for [project context]. After benchmarking
three popular [category] tools, here's what we found.

## What We're Comparing

- **[Tool A]**: [Brief description, version]
- **[Tool B]**: [Brief description, version]
- **[Tool C]**: [Brief description, version]

## Test Methodology

- Environment: [specs]
- Dataset: [description]
- Tests: [what we measured]
- Iterations: [number]

## Benchmark Results

### Test 1: [Scenario]

```
[Setup code]
```

| Tool | Metric 1 | Metric 2 | Metric 3 |
|------|----------|----------|----------|
| A | [value] | [value] | [value] |
| B | [value] | [value] | [value] |
| C | [value] | [value] | [value] |

[Analysis of results]

### Test 2: [Scenario]

[Repeat structure]

## Trade-offs

**Tool A:**
- ✅ Pros: [list]
- ❌ Cons: [list]
- Best for: [use case]

**Tool B:**
- ✅ Pros: [list]
- ❌ Cons: [list]
- Best for: [use case]

**Tool C:**
- ✅ Pros: [list]
- ❌ Cons: [list]
- Best for: [use case]

## Our Choice

We chose [Tool] because [reasoning based on data and our specific needs].

## Full Benchmark Code

[GitHub link]
```

### The "Show HN" Template

```markdown
# Show HN: [Project Name] – [One-line description]

[One paragraph explaining what it is and why it's interesting]

## Why I Built This

[Problem/motivation - keep it real]

## Technical Highlights

### [Interesting aspect 1]

[Explanation with code example]

### [Interesting aspect 2]

[Explanation with code example]

## Architecture

```
[Diagram or description]
```

## Demo

```bash
[Installation and usage examples]
```

[Screenshot or video if applicable]

## Performance

[If relevant - benchmarks or metrics]

## Limitations

[Be honest about what doesn't work yet]

## Links

- GitHub: [url]
- Live demo: [url]
- Docs: [url]

## Discussion

I'd love feedback on [specific aspect]. Also curious if anyone has
solved [related problem] differently.
```

## Advanced Techniques

### Using Data to Tell Stories

**Technique:** Let the data reveal the narrative

**Example:**
```markdown
## What We Discovered

I graphed API latency over 7 days and saw this:

```
Day 1-2: 50ms average
Day 3-4: 55ms average
Day 5:   120ms average (!)
Day 6:   280ms average (!!)
Day 7:   503ms average (timeout hell)
```

The pattern was clear: degradation started on Day 3, accelerated on Day 5.

Overlaying deployment history:
- Day 3: New ORM version deployed
- Day 5: Crossed 1M users milestone

The culprit: The ORM's query builder generated inefficient joins that
scaled poorly. At 1M users, we hit a performance cliff.
```

### The "Rabbit Hole" Technique

**Technique:** Document your journey into deeper complexity

**Example:**
```markdown
## Down the Rabbit Hole

It started as "why is this line slow?" and ended with me reading Linux
kernel source code. Here's the journey:

**Layer 1:** Python code
```python
data = file.read()  # This line takes 2 seconds
```

**Layer 2:** strace shows the syscalls
```
read(3, "..."..., 1000000000)  = 1000000000  <2.134567>
```

**Layer 3:** The filesystem
The file was on a network mount (NFS), not local disk.

**Layer 4:** Network I/O
NFS was using 1KB read chunks. For 1GB = 1M network round trips.

**Layer 5:** NFS mount options
We had `rsize=1024` instead of `rsize=1048576`.

**Solution:**
```bash
mount -o remount,rsize=1048576 /mnt/nfs
```

Read time: 2 seconds → 80ms.

**Lesson:** Always check your assumptions about I/O.
```

### The "Surprising Benchmark" Technique

**Technique:** Challenge common assumptions with data

**Example:**
```markdown
## The Surprising Winner

Common wisdom says "compiled languages are faster than interpreted."
But for this specific task, Python beat C++:

| Language | Runtime | Lines of Code |
|----------|---------|---------------|
| Python | 0.12s | 15 |
| C++ | 1.8s | 87 |

How? The task was parsing JSON. Python's json module is actually C
(using simdjson), while we used a pure C++ parser. The lesson: profile
real code, not assumptions.
```

### The "Evolution" Technique

**Technique:** Show how the solution evolved through iterations

**Example:**
```markdown
## Five Attempts

**v1: Naive approach**
```python
results = [process(x) for x in data]  # 45 seconds
```
Simple but slow.

**v2: Threading**
```python
with ThreadPoolExecutor(10) as pool:
    results = list(pool.map(process, data))  # 43 seconds
```
GIL-bound, no improvement.

**v3: Multiprocessing**
```python
with ProcessPoolExecutor(10) as pool:
    results = list(pool.map(process, data))  # 8 seconds
```
Better! But high memory usage (10 copies of data).

**v4: Memory-mapped files**
```python
with mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as m:
    results = process_mmap(m)  # 5 seconds
```
Faster, shared memory.

**v5: Rust extension**
```rust
#[pyfunction]
fn process_data(data: &[u8]) -> Vec<Result> {
    data.par_iter().map(|x| process(x)).collect()
}  # 0.8 seconds
```

Final speedup: 56x. But v4 (Python + mmap) was good enough for production.
The lesson: optimization has diminishing returns.
```

## Conclusion

HackerNews rewards substance over style, depth over breadth, and honesty over hype. The audience is technically sophisticated and values:

1. **Technical rigor** - Show your work, include code, provide data
2. **Practical insights** - Share hard-won lessons from real experience
3. **Intellectual honesty** - Acknowledge trade-offs, failures, and limitations
4. **Clear communication** - Be direct, skip fluff, respect readers' time
5. **Genuine value** - Teach something non-obvious or share novel approaches

Write for an audience of senior engineers who've seen everything. Surprise them with depth, intrigue them with mysteries, and respect their intelligence.

## When to Use This Skill

✅ **Use this skill when:**
- Writing technical blog posts for developer audiences
- Documenting project postmortems or case studies
- Creating "Show HN" posts for projects
- Writing documentation that needs to be engaging
- Crafting titles for technical content
- Preparing technical talks or presentations
- Contributing to technical discussions

❌ **Don't use this skill for:**
- Marketing copy or sales pages
- Non-technical audiences
- Academic papers (different conventions)
- Internal documentation (different goals)
- Quick notes or drafts (too much overhead)

## Resources

- **HackerNews Guidelines**: https://news.ycombinator.com/newsguidelines.html
- **Analysis of Top Posts**: Study /best to see patterns
- **Title Analysis**: https://hn.algolia.com to search by title patterns
- **Timing Analysis**: https://hnrankings.info for best posting times
- **Writing Style**: Read top technical blogs (Cloudflare, Netflix, Stripe engineering blogs)
