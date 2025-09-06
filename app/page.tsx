"use client"

import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Brain, BookOpen, Target, Zap } from "lucide-react"
import Link from "next/link"

export default function HomePage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-background to-muted">
      {/* Header */}
      <header className="container mx-auto px-4 py-6">
        <nav className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Brain className="h-8 w-8 text-primary" />
            <span className="text-2xl font-bold text-foreground">Active Recall</span>
          </div>
          <Link href="/settings">
            <Button variant="outline" size="sm">
              Pengaturan
            </Button>
          </Link>
        </nav>
      </header>

      {/* Hero Section */}
      <main className="container mx-auto px-4 py-12">
        <div className="text-center max-w-4xl mx-auto animate-in fade-in slide-in-from-bottom-4 duration-600">
          <h1 className="text-5xl md:text-6xl font-bold text-foreground mb-6 text-balance">
            Belajar Lebih Efektif dengan <span className="text-primary">Active Recall</span>
          </h1>

          <p className="text-xl text-muted-foreground mb-8 text-pretty max-w-2xl mx-auto leading-relaxed">
            Tingkatkan daya ingat Anda dengan teknik pembelajaran aktif menggunakan flashcard dan kuis adaptif yang
            disesuaikan dengan kemampuan Anda.
          </p>

          <div className="animate-in fade-in slide-in-from-bottom-4 duration-600 delay-200">
            <Link href="/ingest">
              <Button
                size="lg"
                className="text-lg px-8 py-6 rounded-2xl shadow-lg hover:shadow-xl transition-all duration-300"
              >
                <BookOpen className="mr-2 h-5 w-5" />
                Mulai Belajar
              </Button>
            </Link>
          </div>
        </div>

        {/* Features Section */}
        <div className="mt-20 grid md:grid-cols-3 gap-8 max-w-5xl mx-auto animate-in fade-in slide-in-from-bottom-8 duration-800 delay-400">
          <Card className="rounded-2xl border-0 shadow-lg hover:shadow-xl transition-all duration-300 bg-card/50 backdrop-blur-sm">
            <CardContent className="p-8 text-center">
              <div className="w-16 h-16 bg-primary/10 rounded-2xl flex items-center justify-center mx-auto mb-6">
                <Target className="h-8 w-8 text-primary" />
              </div>
              <h3 className="text-xl font-semibold mb-4 text-card-foreground">Pembelajaran Terarah</h3>
              <p className="text-muted-foreground leading-relaxed">
                Unggah PDF, URL, atau teks untuk membuat flashcard yang disesuaikan dengan materi Anda.
              </p>
            </CardContent>
          </Card>

          <Card className="rounded-2xl border-0 shadow-lg hover:shadow-xl transition-all duration-300 bg-card/50 backdrop-blur-sm">
            <CardContent className="p-8 text-center">
              <div className="w-16 h-16 bg-accent/10 rounded-2xl flex items-center justify-center mx-auto mb-6">
                <Brain className="h-8 w-8 text-accent" />
              </div>
              <h3 className="text-xl font-semibold mb-4 text-card-foreground">Kuis Adaptif</h3>
              <p className="text-muted-foreground leading-relaxed">
                Sistem kuis pintar yang menyesuaikan tingkat kesulitan berdasarkan performa Anda.
              </p>
            </CardContent>
          </Card>

          <Card className="rounded-2xl border-0 shadow-lg hover:shadow-xl transition-all duration-300 bg-card/50 backdrop-blur-sm">
            <CardContent className="p-8 text-center">
              <div className="w-16 h-16 bg-secondary/10 rounded-2xl flex items-center justify-center mx-auto mb-6">
                <Zap className="h-8 w-8 text-secondary" />
              </div>
              <h3 className="text-xl font-semibold mb-4 text-card-foreground">Hasil Cepat</h3>
              <p className="text-muted-foreground leading-relaxed">
                Lacak kemajuan belajar Anda dengan statistik detail dan streak harian.
              </p>
            </CardContent>
          </Card>
        </div>

        {/* How It Works Section */}
        <div className="mt-20 text-center animate-in fade-in slide-in-from-bottom-8 duration-800 delay-600">
          <h2 className="text-3xl font-bold text-foreground mb-12">Cara Kerja</h2>

          <div className="grid md:grid-cols-3 gap-8 max-w-4xl mx-auto">
            <div className="flex flex-col items-center">
              <div className="w-12 h-12 bg-primary rounded-full flex items-center justify-center text-primary-foreground font-bold text-lg mb-4">
                1
              </div>
              <h3 className="text-lg font-semibold mb-2 text-foreground">Unggah Materi</h3>
              <p className="text-muted-foreground text-sm leading-relaxed">
                Upload PDF, paste URL, atau ketik teks yang ingin Anda pelajari
              </p>
            </div>

            <div className="flex flex-col items-center">
              <div className="w-12 h-12 bg-accent rounded-full flex items-center justify-center text-accent-foreground font-bold text-lg mb-4">
                2
              </div>
              <h3 className="text-lg font-semibold mb-2 text-foreground">Buat Flashcard</h3>
              <p className="text-muted-foreground text-sm leading-relaxed">
                AI akan menganalisis materi dan membuat flashcard otomatis
              </p>
            </div>

            <div className="flex flex-col items-center">
              <div className="w-12 h-12 bg-secondary rounded-full flex items-center justify-center text-secondary-foreground font-bold text-lg mb-4">
                3
              </div>
              <h3 className="text-lg font-semibold mb-2 text-foreground">Mulai Kuis</h3>
              <p className="text-muted-foreground text-sm leading-relaxed">
                Latihan dengan kuis adaptif dan lacak kemajuan Anda
              </p>
            </div>
          </div>
        </div>

        {/* CTA Section */}
        <div className="mt-20 text-center animate-in fade-in slide-in-from-bottom-8 duration-800 delay-800">
          <Card className="rounded-2xl border-0 shadow-xl bg-primary/5 backdrop-blur-sm max-w-2xl mx-auto">
            <CardContent className="p-12">
              <h2 className="text-2xl font-bold text-foreground mb-4">Siap Meningkatkan Cara Belajar Anda?</h2>
              <p className="text-muted-foreground mb-8 leading-relaxed">
                Bergabunglah dengan ribuan pelajar yang telah merasakan efektivitas Active Recall
              </p>
              <Link href="/ingest">
                <Button
                  size="lg"
                  className="text-lg px-8 py-6 rounded-2xl shadow-lg hover:shadow-xl transition-all duration-300"
                >
                  Mulai Sekarang - Gratis
                </Button>
              </Link>
            </CardContent>
          </Card>
        </div>
      </main>

      {/* Footer */}
      <footer className="container mx-auto px-4 py-8 mt-20 border-t border-border">
        <div className="text-center text-muted-foreground">
          <p>&copy; 2024 Active Recall. Dibuat dengan ❤️ untuk pembelajaran yang lebih baik.</p>
        </div>
      </footer>
    </div>
  )
}
