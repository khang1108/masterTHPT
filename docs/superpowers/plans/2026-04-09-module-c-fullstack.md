# Module C: Fullstack (NestJS + Next.js) — Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the NestJS backend API (auth, exam CRUD, session management, agent dispatch, file upload) and the Next.js frontend (login, dashboard, exam room with timer, results with error analysis, upload page).

**Architecture:** NestJS at port 3001 serves as the API gateway — it authenticates users, manages exam data in MongoDB, proxies requests to Agent Service, and stores results. Next.js at port 3000 is the student-facing UI with SSR support.

**Tech Stack:** NestJS, Mongoose, JWT, multer, Next.js 14 (App Router), TailwindCSS, shadcn/ui, React Query

**Owner:** Nguyên Huy (Fullstack Developer)

**Dependency:** None — can work fully independently using mock data.

---

## File Structure

```
master/apps/api/
├── src/
│   ├── main.ts
│   ├── app.module.ts
│   ├── common/
│   │   ├── guards/
│   │   │   └── jwt-auth.guard.ts
│   │   ├── decorators/
│   │   │   └── current-user.decorator.ts
│   │   └── pipes/
│   ├── database/
│   │   ├── database.module.ts
│   │   └── schemas/
│   │       ├── student.schema.ts
│   │       ├── exam.schema.ts
│   │       ├── exam-session.schema.ts
│   │       ├── knowledge-node.schema.ts
│   │       └── rubric.schema.ts
│   ├── auth/
│   │   ├── auth.module.ts
│   │   ├── auth.controller.ts
│   │   ├── auth.service.ts
│   │   └── dto/
│   │       ├── register.dto.ts
│   │       └── login.dto.ts
│   ├── exams/
│   │   ├── exams.module.ts
│   │   ├── exams.controller.ts
│   │   ├── exams.service.ts
│   │   └── dto/
│   │       ├── create-session.dto.ts
│   │       └── submit-session.dto.ts
│   ├── upload/
│   │   ├── upload.module.ts
│   │   └── upload.controller.ts
│   ├── students/
│   │   ├── students.module.ts
│   │   ├── students.controller.ts
│   │   └── students.service.ts
│   └── agent-dispatch/
│       ├── agent-dispatch.module.ts
│       └── agent-dispatch.service.ts
├── test/
├── package.json
├── tsconfig.json
├── nest-cli.json
└── Dockerfile

master/apps/web/
├── src/
│   ├── app/
│   │   ├── layout.tsx
│   │   ├── page.tsx                    ← Landing / redirect
│   │   ├── login/page.tsx
│   │   ├── register/page.tsx
│   │   ├── dashboard/page.tsx
│   │   ├── exams/
│   │   │   ├── page.tsx               ← Exam list
│   │   │   └── [id]/
│   │   │       ├── page.tsx           ← Exam room
│   │   │       └── results/page.tsx   ← Results + error analysis
│   │   ├── upload/page.tsx
│   │   └── profile/page.tsx
│   ├── components/
│   │   ├── ui/                        ← shadcn components
│   │   ├── exam-timer.tsx
│   │   ├── question-card.tsx
│   │   ├── question-nav.tsx
│   │   ├── result-summary.tsx
│   │   ├── error-analysis-card.tsx
│   │   └── file-upload.tsx
│   ├── lib/
│   │   ├── api.ts                     ← Axios client
│   │   └── auth.ts                    ← JWT helpers
│   └── hooks/
│       ├── use-auth.ts
│       ├── use-exam.ts
│       └── use-timer.ts
├── package.json
├── tailwind.config.ts
├── tsconfig.json
└── Dockerfile
```

---

## Chunk 1: NestJS Backend API

### Task 1: Init NestJS + MongoDB

**Files:**
- Create: `master/apps/api/` (NestJS project)

- [ ] **Step 1: Scaffold NestJS project**

Run:
```bash
cd master/apps
npx @nestjs/cli new api --package-manager npm --skip-git
cd api
npm install @nestjs/mongoose mongoose
npm install @nestjs/jwt @nestjs/passport passport passport-jwt bcryptjs
npm install @nestjs/config class-validator class-transformer
npm install -D @types/passport-jwt @types/bcryptjs
```

- [ ] **Step 2: Configure MongoDB connection**

```typescript
// master/apps/api/src/database/database.module.ts
import { Module } from '@nestjs/common';
import { MongooseModule } from '@nestjs/mongoose';
import { ConfigService } from '@nestjs/config';

@Module({
  imports: [
    MongooseModule.forRootAsync({
      inject: [ConfigService],
      useFactory: (config: ConfigService) => ({
        uri: config.get<string>('MONGODB_URI', 'mongodb://master:master_dev_pw@localhost:27017/master_db?authSource=admin'),
      }),
    }),
  ],
})
export class DatabaseModule {}
```

- [ ] **Step 3: Define Mongoose schemas**

```typescript
// master/apps/api/src/database/schemas/student.schema.ts
import { Prop, Schema, SchemaFactory } from '@nestjs/mongoose';
import { Document } from 'mongoose';

@Schema({ timestamps: true })
export class Student extends Document {
  @Prop({ required: true, unique: true })
  email: string;

  @Prop({ required: true })
  name: string;

  @Prop({ required: true })
  password_hash: string;

  @Prop({ required: true, enum: [10, 11, 12] })
  grade: number;

  @Prop({
    type: {
      theta: { type: Number, default: 0.0 },
      theta_se: { type: Number, default: 1.0 },
      total_items: { type: Number, default: 0 },
    },
    default: { theta: 0.0, theta_se: 1.0, total_items: 0 },
  })
  irt_profile: {
    theta: number;
    theta_se: number;
    total_items: number;
  };

  @Prop({ type: Object, default: {} })
  mastery_scores: Record<string, {
    p_l: number;
    total_attempts: number;
    correct_attempts: number;
    updated_at: Date;
  }>;
}

export const StudentSchema = SchemaFactory.createForClass(Student);
```

```typescript
// master/apps/api/src/database/schemas/exam.schema.ts
import { Prop, Schema, SchemaFactory } from '@nestjs/mongoose';
import { Document } from 'mongoose';

@Schema({ timestamps: true })
export class Exam extends Document {
  @Prop({ required: true })
  subject: string;

  @Prop({ required: true })
  exam_type: string;

  @Prop()
  year: number;

  @Prop()
  source: string;

  @Prop({ required: true })
  total_questions: number;

  @Prop()
  duration_minutes: number;

  @Prop({ type: Array, required: true })
  sections: Array<{
    type: string;
    questions: Array<{
      id: string;
      question_index: number;
      type: string;
      content: string;
      content_latex?: string;
      options?: string[];
      correct_answer?: string;
      has_image: boolean;
      image_url?: string;
      difficulty_a: number;
      difficulty_b: number;
      topic_tags: string[];
      max_score: number;
    }>;
  }>;

  @Prop({ type: Object })
  metadata: Record<string, any>;
}

export const ExamSchema = SchemaFactory.createForClass(Exam);
```

```typescript
// master/apps/api/src/database/schemas/exam-session.schema.ts
import { Prop, Schema, SchemaFactory } from '@nestjs/mongoose';
import { Document, Types } from 'mongoose';

@Schema({ timestamps: true })
export class ExamSession extends Document {
  @Prop({ type: Types.ObjectId, ref: 'Student', required: true })
  student_id: Types.ObjectId;

  @Prop({ type: Types.ObjectId, ref: 'Exam', required: true })
  exam_id: Types.ObjectId;

  @Prop({ required: true, enum: ['EXAM_PRACTICE', 'GRADE_SUBMISSION'] })
  intent: string;

  @Prop({ required: true, enum: ['IN_PROGRESS', 'SUBMITTED', 'GRADED'], default: 'IN_PROGRESS' })
  status: string;

  @Prop()
  started_at: Date;

  @Prop()
  submitted_at: Date;

  @Prop({ type: Object, default: {} })
  student_answers: Record<string, string>;

  @Prop()
  uploaded_file_url: string;

  @Prop({ type: Object })
  evaluation: Record<string, any>;

  @Prop({ type: [String], default: [] })
  agent_trail: string[];
}

export const ExamSessionSchema = SchemaFactory.createForClass(ExamSession);
```

- [ ] **Step 4: Update app.module.ts**

```typescript
// master/apps/api/src/app.module.ts
import { Module } from '@nestjs/common';
import { ConfigModule } from '@nestjs/config';
import { DatabaseModule } from './database/database.module';
import { AuthModule } from './auth/auth.module';
import { ExamsModule } from './exams/exams.module';
import { UploadModule } from './upload/upload.module';
import { StudentsModule } from './students/students.module';

@Module({
  imports: [
    ConfigModule.forRoot({ isGlobal: true }),
    DatabaseModule,
    AuthModule,
    ExamsModule,
    UploadModule,
    StudentsModule,
  ],
})
export class AppModule {}
```

- [ ] **Step 5: Commit**

```bash
git add master/apps/api/
git commit -m "feat(api): init NestJS with MongoDB, Mongoose schemas for students/exams/sessions"
```

---

### Task 2: Auth Module (Register + Login + JWT)

**Files:**
- Create: `master/apps/api/src/auth/`

- [ ] **Step 1: Write DTOs**

```typescript
// master/apps/api/src/auth/dto/register.dto.ts
import { IsEmail, IsString, MinLength, IsIn } from 'class-validator';

export class RegisterDto {
  @IsEmail()
  email: string;

  @IsString()
  @MinLength(2)
  name: string;

  @IsString()
  @MinLength(6)
  password: string;

  @IsIn([10, 11, 12])
  grade: number;
}
```

```typescript
// master/apps/api/src/auth/dto/login.dto.ts
import { IsEmail, IsString } from 'class-validator';

export class LoginDto {
  @IsEmail()
  email: string;

  @IsString()
  password: string;
}
```

- [ ] **Step 2: Write AuthService**

```typescript
// master/apps/api/src/auth/auth.service.ts
import { Injectable, ConflictException, UnauthorizedException } from '@nestjs/common';
import { InjectModel } from '@nestjs/mongoose';
import { Model } from 'mongoose';
import { JwtService } from '@nestjs/jwt';
import * as bcrypt from 'bcryptjs';
import { Student } from '../database/schemas/student.schema';
import { RegisterDto } from './dto/register.dto';
import { LoginDto } from './dto/login.dto';

@Injectable()
export class AuthService {
  constructor(
    @InjectModel(Student.name) private studentModel: Model<Student>,
    private jwtService: JwtService,
  ) {}

  async register(dto: RegisterDto) {
    const existing = await this.studentModel.findOne({ email: dto.email });
    if (existing) throw new ConflictException('Email already registered');

    const hash = await bcrypt.hash(dto.password, 10);
    const student = await this.studentModel.create({
      email: dto.email,
      name: dto.name,
      password_hash: hash,
      grade: dto.grade,
    });

    return { id: student._id, email: student.email, name: student.name };
  }

  async login(dto: LoginDto) {
    const student = await this.studentModel.findOne({ email: dto.email });
    if (!student) throw new UnauthorizedException('Invalid credentials');

    const valid = await bcrypt.compare(dto.password, student.password_hash);
    if (!valid) throw new UnauthorizedException('Invalid credentials');

    const payload = { sub: student._id, email: student.email };
    const token = this.jwtService.sign(payload);

    return { access_token: token, student: { id: student._id, name: student.name, email: student.email } };
  }
}
```

- [ ] **Step 3: Write AuthController**

```typescript
// master/apps/api/src/auth/auth.controller.ts
import { Controller, Post, Body } from '@nestjs/common';
import { AuthService } from './auth.service';
import { RegisterDto } from './dto/register.dto';
import { LoginDto } from './dto/login.dto';

@Controller('auth')
export class AuthController {
  constructor(private authService: AuthService) {}

  @Post('register')
  register(@Body() dto: RegisterDto) {
    return this.authService.register(dto);
  }

  @Post('login')
  login(@Body() dto: LoginDto) {
    return this.authService.login(dto);
  }
}
```

- [ ] **Step 4: Write JWT strategy + guard**

```typescript
// master/apps/api/src/common/guards/jwt-auth.guard.ts
import { Injectable, ExecutionContext, UnauthorizedException } from '@nestjs/common';
import { AuthGuard } from '@nestjs/passport';

@Injectable()
export class JwtAuthGuard extends AuthGuard('jwt') {
  handleRequest(err: any, user: any) {
    if (err || !user) throw new UnauthorizedException();
    return user;
  }
}
```

- [ ] **Step 5: Write AuthModule**

```typescript
// master/apps/api/src/auth/auth.module.ts
import { Module } from '@nestjs/common';
import { JwtModule } from '@nestjs/jwt';
import { PassportModule } from '@nestjs/passport';
import { MongooseModule } from '@nestjs/mongoose';
import { ConfigService } from '@nestjs/config';
import { AuthController } from './auth.controller';
import { AuthService } from './auth.service';
import { Student, StudentSchema } from '../database/schemas/student.schema';

@Module({
  imports: [
    PassportModule,
    MongooseModule.forFeature([{ name: Student.name, schema: StudentSchema }]),
    JwtModule.registerAsync({
      inject: [ConfigService],
      useFactory: (config: ConfigService) => ({
        secret: config.get('JWT_SECRET', 'hackathon-dev-secret'),
        signOptions: { expiresIn: '7d' },
      }),
    }),
  ],
  controllers: [AuthController],
  providers: [AuthService],
  exports: [AuthService, JwtModule],
})
export class AuthModule {}
```

- [ ] **Step 6: Test auth endpoints**

Run:
```bash
cd master/apps/api && npm run start:dev
```

Test:
```bash
# Register
curl -X POST http://localhost:3001/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@test.com","name":"Test","password":"123456","grade":12}'

# Login
curl -X POST http://localhost:3001/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@test.com","password":"123456"}'
```

Expected: Register returns `{id, email, name}`. Login returns `{access_token, student}`.

- [ ] **Step 7: Commit**

```bash
git add master/apps/api/src/auth/ master/apps/api/src/common/
git commit -m "feat(api): add auth module with register, login, JWT"
```

---

### Task 3: Agent Dispatch Service

**Files:**
- Create: `master/apps/api/src/agent-dispatch/`

- [ ] **Step 1: Write dispatch service**

```typescript
// master/apps/api/src/agent-dispatch/agent-dispatch.service.ts
import { Injectable, Logger } from '@nestjs/common';
import { ConfigService } from '@nestjs/config';

interface TaskRequest {
  student_id: string;
  intent: string;
  user_message: string;
  session_id?: string;
  file_urls?: string[];
  metadata?: Record<string, any>;
}

interface TaskResponse {
  task_id: string;
  status: 'success' | 'error';
  intent: string;
  result: Record<string, any>;
  agent_trail: string[];
  error_message?: string;
}

@Injectable()
export class AgentDispatchService {
  private readonly logger = new Logger(AgentDispatchService.name);
  private readonly agentUrl: string;

  constructor(private config: ConfigService) {
    this.agentUrl = config.get('AGENT_SERVICE_URL', 'http://localhost:8000');
  }

  async dispatch(request: TaskRequest): Promise<TaskResponse> {
    const url = `${this.agentUrl}/api/agents/dispatch`;
    this.logger.log(`Dispatching to agent: intent=${request.intent}`);

    try {
      const response = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(request),
      });

      if (!response.ok) {
        throw new Error(`Agent service returned ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      this.logger.error(`Agent dispatch failed: ${error.message}`);
      return {
        task_id: '',
        status: 'error',
        intent: request.intent,
        result: {},
        agent_trail: [],
        error_message: error.message,
      };
    }
  }
}
```

```typescript
// master/apps/api/src/agent-dispatch/agent-dispatch.module.ts
import { Module } from '@nestjs/common';
import { AgentDispatchService } from './agent-dispatch.service';

@Module({
  providers: [AgentDispatchService],
  exports: [AgentDispatchService],
})
export class AgentDispatchModule {}
```

- [ ] **Step 2: Commit**

```bash
git add master/apps/api/src/agent-dispatch/
git commit -m "feat(api): add agent dispatch service for HTTP proxy to Agent Service"
```

---

### Task 4: Exams Module (CRUD + Session + Submit)

**Files:**
- Create: `master/apps/api/src/exams/`

- [ ] **Step 1: Write ExamsService**

```typescript
// master/apps/api/src/exams/exams.service.ts
import { Injectable, NotFoundException } from '@nestjs/common';
import { InjectModel } from '@nestjs/mongoose';
import { Model, Types } from 'mongoose';
import { Exam } from '../database/schemas/exam.schema';
import { ExamSession } from '../database/schemas/exam-session.schema';
import { Student } from '../database/schemas/student.schema';
import { AgentDispatchService } from '../agent-dispatch/agent-dispatch.service';

@Injectable()
export class ExamsService {
  constructor(
    @InjectModel(Exam.name) private examModel: Model<Exam>,
    @InjectModel(ExamSession.name) private sessionModel: Model<ExamSession>,
    @InjectModel(Student.name) private studentModel: Model<Student>,
    private agentDispatch: AgentDispatchService,
  ) {}

  async findAll(filters: { subject?: string; exam_type?: string }) {
    const query: Record<string, any> = {};
    if (filters.subject) query.subject = filters.subject;
    if (filters.exam_type) query.exam_type = filters.exam_type;
    return this.examModel.find(query).select('-sections.questions.correct_answer').exec();
  }

  async findById(id: string) {
    const exam = await this.examModel.findById(id).exec();
    if (!exam) throw new NotFoundException('Exam not found');
    return exam;
  }

  async createSession(studentId: string, examId: string, intent: string = 'EXAM_PRACTICE') {
    const exam = await this.examModel.findById(examId);
    if (!exam) throw new NotFoundException('Exam not found');

    const session = await this.sessionModel.create({
      student_id: new Types.ObjectId(studentId),
      exam_id: new Types.ObjectId(examId),
      intent,
      status: 'IN_PROGRESS',
      started_at: new Date(),
    });
    return session;
  }

  async submitSession(sessionId: string, studentId: string, answers: Record<string, string>, fileUrl?: string) {
    const session = await this.sessionModel.findById(sessionId);
    if (!session) throw new NotFoundException('Session not found');

    session.student_answers = answers;
    session.submitted_at = new Date();
    session.status = 'SUBMITTED';
    if (fileUrl) session.uploaded_file_url = fileUrl;
    await session.save();

    const result = await this.agentDispatch.dispatch({
      student_id: studentId,
      intent: fileUrl ? 'GRADE_SUBMISSION' : 'GRADE_SUBMISSION',
      user_message: 'Grade my submission',
      session_id: sessionId,
      file_urls: fileUrl ? [fileUrl] : [],
      metadata: {
        subject: 'math',
        student_answers: answers,
      },
    });

    if (result.status === 'success') {
      session.evaluation = result.result;
      session.agent_trail = result.agent_trail;
      session.status = 'GRADED';
      await session.save();
    }

    return { session_id: sessionId, status: session.status, evaluation: session.evaluation };
  }

  async getSessionResults(sessionId: string) {
    const session = await this.sessionModel.findById(sessionId).populate('exam_id').exec();
    if (!session) throw new NotFoundException('Session not found');
    return session;
  }
}
```

- [ ] **Step 2: Write ExamsController**

```typescript
// master/apps/api/src/exams/exams.controller.ts
import { Controller, Get, Post, Param, Body, Query, UseGuards, Req } from '@nestjs/common';
import { JwtAuthGuard } from '../common/guards/jwt-auth.guard';
import { ExamsService } from './exams.service';

@Controller('exams')
export class ExamsController {
  constructor(private examsService: ExamsService) {}

  @Get()
  findAll(@Query('subject') subject?: string, @Query('exam_type') examType?: string) {
    return this.examsService.findAll({ subject, exam_type: examType });
  }

  @Get(':id')
  findById(@Param('id') id: string) {
    return this.examsService.findById(id);
  }

  @UseGuards(JwtAuthGuard)
  @Post('sessions')
  createSession(@Body() body: { exam_id: string; intent?: string }, @Req() req: any) {
    return this.examsService.createSession(req.user.sub, body.exam_id, body.intent);
  }

  @UseGuards(JwtAuthGuard)
  @Post('sessions/:id/submit')
  submitSession(
    @Param('id') id: string,
    @Body() body: { answers: Record<string, string>; file_url?: string },
    @Req() req: any,
  ) {
    return this.examsService.submitSession(id, req.user.sub, body.answers, body.file_url);
  }

  @UseGuards(JwtAuthGuard)
  @Get('sessions/:id/results')
  getResults(@Param('id') id: string) {
    return this.examsService.getSessionResults(id);
  }
}
```

- [ ] **Step 3: Write ExamsModule**

```typescript
// master/apps/api/src/exams/exams.module.ts
import { Module } from '@nestjs/common';
import { MongooseModule } from '@nestjs/mongoose';
import { ExamsController } from './exams.controller';
import { ExamsService } from './exams.service';
import { Exam, ExamSchema } from '../database/schemas/exam.schema';
import { ExamSession, ExamSessionSchema } from '../database/schemas/exam-session.schema';
import { Student, StudentSchema } from '../database/schemas/student.schema';
import { AgentDispatchModule } from '../agent-dispatch/agent-dispatch.module';

@Module({
  imports: [
    MongooseModule.forFeature([
      { name: Exam.name, schema: ExamSchema },
      { name: ExamSession.name, schema: ExamSessionSchema },
      { name: Student.name, schema: StudentSchema },
    ]),
    AgentDispatchModule,
  ],
  controllers: [ExamsController],
  providers: [ExamsService],
})
export class ExamsModule {}
```

- [ ] **Step 4: Commit**

```bash
git add master/apps/api/src/exams/
git commit -m "feat(api): add exams module — CRUD, session management, agent dispatch on submit"
```

---

### Task 5: Upload + Students modules

(Abbreviated — follow same pattern as above)

- [ ] **Step 1: Upload module** — accept multipart file, save to `uploads/` folder, return path
- [ ] **Step 2: Students module** — `GET /students/me/profile`, `GET /students/me/history`
- [ ] **Step 3: Commit**

```bash
git commit -m "feat(api): add upload and students profile modules"
```

---

## Chunk 2: Next.js Frontend

### Task 6: Init Next.js + shadcn/ui

- [ ] **Step 1: Scaffold**

Run:
```bash
cd master/apps
npx create-next-app@latest web --typescript --tailwind --eslint --app --src-dir
cd web
npx shadcn-ui@latest init
npx shadcn-ui@latest add button card input label badge tabs progress
npm install axios @tanstack/react-query lucide-react
```

- [ ] **Step 2: Create API client**

```typescript
// master/apps/web/src/lib/api.ts
import axios from 'axios';

const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:3001',
});

api.interceptors.request.use((config) => {
  if (typeof window !== 'undefined') {
    const token = localStorage.getItem('token');
    if (token) config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export default api;
```

- [ ] **Step 3: Commit**

```bash
git add master/apps/web/
git commit -m "feat(web): init Next.js 14 with shadcn/ui, TailwindCSS, API client"
```

---

### Task 7: Login / Register Pages

- [ ] **Step 1: Login page**

```tsx
// master/apps/web/src/app/login/page.tsx
'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import api from '@/lib/api';

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    try {
      const { data } = await api.post('/auth/login', { email, password });
      localStorage.setItem('token', data.access_token);
      localStorage.setItem('user', JSON.stringify(data.student));
      router.push('/dashboard');
    } catch (err: any) {
      setError(err.response?.data?.message || 'Đăng nhập thất bại');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100">
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle className="text-2xl text-center">MASTER</CardTitle>
          <p className="text-center text-muted-foreground">Đăng nhập để bắt đầu ôn thi</p>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <Label htmlFor="email">Email</Label>
              <Input id="email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
            </div>
            <div>
              <Label htmlFor="password">Mật khẩu</Label>
              <Input id="password" type="password" value={password} onChange={(e) => setPassword(e.target.value)} required />
            </div>
            {error && <p className="text-red-500 text-sm">{error}</p>}
            <Button type="submit" className="w-full" disabled={loading}>
              {loading ? 'Đang đăng nhập...' : 'Đăng nhập'}
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
```

- [ ] **Step 2: Commit**

```bash
git commit -m "feat(web): add login and register pages"
```

---

### Task 8: Dashboard Page

- [ ] **Step 1: Create dashboard**

The dashboard shows:
- Student name + grade
- 3 action cards: "Luyện thi" (exam practice), "Nộp bài chấm" (upload & grade), "Phân tích năng lực" (view analysis)
- Recent exam history

- [ ] **Step 2: Commit**

```bash
git commit -m "feat(web): add dashboard with action cards and exam history"
```

---

### Task 9: Exam Room (Most Complex Page)

Key components:
- **Countdown timer** (auto-submit when time runs out)
- **Question navigation panel** (left sidebar, marks answered questions)
- **Question display** (content + 4 MC options)
- **Submit button**

- [ ] **Step 1: Create ExamTimer component**

```tsx
// master/apps/web/src/components/exam-timer.tsx
'use client';

import { useState, useEffect, useCallback } from 'react';

interface ExamTimerProps {
  durationMinutes: number;
  onTimeUp: () => void;
}

export function ExamTimer({ durationMinutes, onTimeUp }: ExamTimerProps) {
  const [secondsLeft, setSecondsLeft] = useState(durationMinutes * 60);

  useEffect(() => {
    if (secondsLeft <= 0) {
      onTimeUp();
      return;
    }
    const timer = setInterval(() => setSecondsLeft((s) => s - 1), 1000);
    return () => clearInterval(timer);
  }, [secondsLeft, onTimeUp]);

  const minutes = Math.floor(secondsLeft / 60);
  const seconds = secondsLeft % 60;
  const isWarning = secondsLeft < 300; // last 5 minutes

  return (
    <div className={`text-2xl font-mono font-bold ${isWarning ? 'text-red-600 animate-pulse' : 'text-gray-800'}`}>
      {String(minutes).padStart(2, '0')}:{String(seconds).padStart(2, '0')}
    </div>
  );
}
```

- [ ] **Step 2: Create QuestionCard component**

```tsx
// master/apps/web/src/components/question-card.tsx
'use client';

interface QuestionCardProps {
  question: {
    id: string;
    question_index: number;
    content: string;
    options?: string[];
    type: string;
  };
  selectedAnswer?: string;
  onAnswer: (questionId: string, answer: string) => void;
}

export function QuestionCard({ question, selectedAnswer, onAnswer }: QuestionCardProps) {
  return (
    <div className="p-6">
      <h3 className="text-lg font-medium mb-4">
        Câu {question.question_index}: {question.content}
      </h3>
      {question.options && (
        <div className="space-y-3">
          {question.options.map((option, idx) => {
            const letter = option.charAt(0);
            const isSelected = selectedAnswer === letter;
            return (
              <button
                key={idx}
                onClick={() => onAnswer(question.id, letter)}
                className={`w-full text-left p-3 rounded-lg border transition-colors
                  ${isSelected
                    ? 'border-blue-500 bg-blue-50 text-blue-800'
                    : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
                  }`}
              >
                {option}
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
}
```

- [ ] **Step 3: Create exam room page**

The exam room page at `master/apps/web/src/app/exams/[id]/page.tsx`:
- Fetches exam data from API
- Renders timer, question nav, question content
- Tracks answers in state
- Submits on button click or timer end
- Redirects to results page after submission

- [ ] **Step 4: Commit**

```bash
git commit -m "feat(web): add exam room with timer, question navigation, and auto-submit"
```

---

### Task 10: Results Page with Error Analysis

- [ ] **Step 1: Create result components**

The results page at `master/apps/web/src/app/exams/[id]/results/page.tsx` shows:
- Score summary (total/max, percentage, colored badge)
- Per-question breakdown (correct/wrong indicator, reasoning)
- Error analysis cards for wrong answers (error type badge, root cause, remedial)
- Strengths/weaknesses summary
- "Ôn tập lại" button for recommended topics

- [ ] **Step 2: Create ErrorAnalysisCard component**

```tsx
// master/apps/web/src/components/error-analysis-card.tsx
'use client';

import { Badge } from '@/components/ui/badge';

const ERROR_TYPE_LABELS: Record<string, { label: string; color: string }> = {
  CONCEPT_GAP: { label: 'Hổng kiến thức', color: 'bg-red-100 text-red-800' },
  CALCULATION_ERROR: { label: 'Sai tính toán', color: 'bg-orange-100 text-orange-800' },
  INCOMPLETE_REASONING: { label: 'Thiếu bước giải', color: 'bg-yellow-100 text-yellow-800' },
  MISINTERPRETATION: { label: 'Hiểu sai đề', color: 'bg-purple-100 text-purple-800' },
  PRESENTATION_FLAW: { label: 'Trình bày chưa rõ', color: 'bg-blue-100 text-blue-800' },
};

interface ErrorAnalysisCardProps {
  error: {
    error_type: string;
    root_cause: string;
    knowledge_component: string;
    remedial: string;
  };
}

export function ErrorAnalysisCard({ error }: ErrorAnalysisCardProps) {
  const typeInfo = ERROR_TYPE_LABELS[error.error_type] || { label: error.error_type, color: 'bg-gray-100' };

  return (
    <div className="border rounded-lg p-4 bg-red-50/50">
      <div className="flex items-center gap-2 mb-2">
        <Badge className={typeInfo.color}>{typeInfo.label}</Badge>
        <span className="text-sm text-muted-foreground">{error.knowledge_component}</span>
      </div>
      <p className="text-sm mb-1"><strong>Nguyên nhân:</strong> {error.root_cause}</p>
      <p className="text-sm text-blue-700"><strong>Gợi ý ôn tập:</strong> {error.remedial}</p>
    </div>
  );
}
```

- [ ] **Step 3: Commit**

```bash
git commit -m "feat(web): add results page with score summary and error analysis cards"
```

---

### Task 11: Upload Page

- [ ] **Step 1: Create drag-and-drop file upload**
- [ ] **Step 2: Commit**

```bash
git commit -m "feat(web): add upload page with drag-and-drop file upload"
```

---

## Summary — What Nguyên Huy Delivers

| Day | Deliverable |
|-----|-------------|
| 1 | NestJS init + MongoDB schemas + database module |
| 2 | Auth module (register/login/JWT) |
| 3 | Agent dispatch service + Exams module |
| 4 | Upload module + Students module |
| 5 | Next.js init + API client + login/register pages |
| 6 | Dashboard page |
| 7-8 | Exam room (timer, question nav, submit) |
| 9 | Results page with error analysis |
| 10 | Upload page + integration testing |
| 11-12 | UI polish, responsive design, demo prep |
