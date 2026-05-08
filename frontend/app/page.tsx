import Link from 'next/link';
import { Shell } from '@/components/Shell';

const features = [
  {
    title: 'Tư vấn hỏi đáp tức thì',
    body: 'Đặt câu hỏi bằng ngôn ngữ tự nhiên và nhận phản hồi bám sát dữ liệu tuyển sinh đã chuẩn hóa.',
  },
  {
    title: 'Tra cứu có cấu trúc',
    body: 'Lọc nhanh theo trường, ngành, mã ngành và tổ hợp để so sánh thông tin một cách trực quan.',
  },
  {
    title: 'Độ tin cậy cao',
    body: 'Hệ thống ưu tiên nguồn dữ liệu nội bộ trước khi sinh câu trả lời, giảm nhiễu và giữ tính nhất quán.',
  },
];

const stats = [
  { label: 'Dữ liệu chuẩn hóa', value: '100% có cấu trúc' },
  { label: 'Phản hồi nhanh', value: '< 2 giây trung bình' },
  { label: 'Luồng tra cứu', value: 'Chat + Bảng dữ liệu' },
];

export default function HomePage() {
  return (
    <Shell>
      <section className="landing-hero relative overflow-hidden rounded-3xl border border-teal-100/80 p-6 shadow-panel sm:p-10">
        <div className="landing-orb landing-orb-left" aria-hidden="true" />
        <div className="landing-orb landing-orb-right" aria-hidden="true" />

        <div className="relative z-10 grid items-center gap-8 lg:grid-cols-[1.1fr_0.9fr]">
          <div className="animate-fade-up space-y-6">
            <p className="inline-flex rounded-full border border-teal-200 bg-teal-50 px-3 py-1 text-xs font-semibold uppercase tracking-[0.2em] text-teal-700">
              admission intelligence platform
            </p>
            <h1 className="max-w-3xl font-heading text-3xl font-semibold leading-tight text-slate-900 sm:text-5xl">
              Landing page tuyển sinh hiện đại, giúp ra quyết định nhanh và chính xác
            </h1>
            <p className="max-w-2xl text-sm text-slate-700 sm:text-base">
              Kết hợp AI hỏi đáp và bảng tra cứu dữ liệu trong một giao diện trực quan, chuyên
              nghiệp, tối ưu cho cả học sinh, phụ huynh và đội ngũ tư vấn.
            </p>
            <div className="flex flex-wrap gap-3">
              <Link
                href="/chatbot"
                className="rounded-xl bg-teal-700 px-5 py-2.5 text-sm font-semibold text-white transition hover:-translate-y-0.5 hover:bg-teal-800"
              >
                Trải nghiệm chatbot
              </Link>
              <Link
                href="/tra-cuu"
                className="rounded-xl border border-slate-300 bg-white px-5 py-2.5 text-sm font-semibold text-slate-800 transition hover:-translate-y-0.5 hover:border-slate-400"
              >
                Mở bảng tra cứu
              </Link>
            </div>
            <div className="grid gap-3 pt-2 sm:grid-cols-3">
              {stats.map((item) => (
                <article
                  key={item.label}
                  className="rounded-2xl border border-white/70 bg-white/75 p-3 backdrop-blur"
                >
                  <p className="text-xs uppercase tracking-wide text-slate-500">{item.label}</p>
                  <p className="mt-1 text-sm font-semibold text-slate-900">{item.value}</p>
                </article>
              ))}
            </div>
          </div>

          <aside className="landing-tilt-card mx-auto w-full max-w-md rounded-3xl border border-teal-200/60 bg-white/90 p-5 shadow-2xl">
            <div className="landing-card-glow" aria-hidden="true" />
            <div className="relative space-y-4">
              <div className="flex items-center justify-between">
                <p className="text-sm font-semibold text-slate-800">Dashboard tư vấn</p>
                <span className="rounded-full bg-teal-100 px-2.5 py-1 text-xs font-semibold text-teal-700">
                  realtime
                </span>
              </div>
              <div className="rounded-2xl border border-slate-200 bg-slate-50 p-3">
                <p className="text-xs text-slate-500">Câu hỏi nổi bật</p>
                <p className="mt-1 text-sm text-slate-800">
                  Học phí ngành Công nghệ thông tin của trường X năm 2025 là bao nhiêu?
                </p>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div className="rounded-2xl border border-teal-100 bg-teal-50/70 p-3">
                  <p className="text-xs text-teal-700">Tỉ lệ có dữ liệu</p>
                  <p className="mt-1 text-lg font-semibold text-teal-900">94%</p>
                </div>
                <div className="rounded-2xl border border-sky-100 bg-sky-50 p-3">
                  <p className="text-xs text-sky-700">Ngành đã index</p>
                  <p className="mt-1 text-lg font-semibold text-sky-900">120+</p>
                </div>
              </div>
            </div>
          </aside>
        </div>
      </section>

      <section className="mt-6 grid gap-4 sm:grid-cols-3">
        {features.map((feature, idx) => (
          <article
            key={feature.title}
            className="animate-fade-up rounded-2xl border border-slate-200 bg-white/85 p-5 transition hover:-translate-y-1 hover:border-teal-200"
            style={{ animationDelay: `${idx * 100}ms` }}
          >
            <h3 className="text-sm font-semibold text-slate-900">{feature.title}</h3>
            <p className="mt-2 text-sm leading-relaxed text-slate-700">{feature.body}</p>
          </article>
        ))}
      </section>
    </Shell>
  );
}
