import { useState } from "react";
import {
  AlertCircle,
  ArrowLeft,
  ArrowRight,
  CheckCircle2,
  MapPin,
  Navigation,
  Package,
} from "lucide-react";

type Recipient = { name: string; phone: string; email: string; comment: string };
type Payment = "cash" | "card";

const inputClass =
  "w-full rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm outline-none focus:border-emerald-500 focus:ring-2 focus:ring-emerald-100";
const fieldLabels = [
  "Имя и фамилия",
  "Телефон",
  "Электронная почта (необязательно)",
  "Комментарий курьеру (необязательно)",
];

export default function Delivery() {
  const [step, setStep] = useState(1);
  const [rawAddress, setRawAddress] = useState("");
  const [checked, setChecked] = useState(false);
  const [recipient, setRecipient] = useState<Recipient>({ name: "", phone: "", email: "", comment: "" });
  const [payment, setPayment] = useState<Payment | "">("");
  const [error, setError] = useState("");
  const [submitted, setSubmitted] = useState(false);

  function checkAddress() {
    if (!rawAddress.trim()) {
      setError("Введите адрес доставки.");
      setChecked(false);
      return;
    }
    setError("");
    setChecked(true);
  }

  function continueStep() {
    setError("");
    if (step === 1) {
      if (!checked) {
        setError("Сначала укажите адрес и нажмите «Проверить адрес».");
        return;
      }
      setStep(2);
    } else if (step === 2) {
      if (!recipient.name.trim() || !recipient.phone.trim()) {
        setError("Укажите имя получателя и номер телефона.");
        return;
      }
      setStep(3);
    } else {
      if (!payment) {
        setError("Выберите способ оплаты.");
        return;
      }
      setSubmitted(true);
    }
  }

  const steps = ["Адрес", "Получатель", "Оплата"];
  const recipientValues: (keyof Recipient)[] = ["name", "phone", "email", "comment"];

  return (
    <div className="space-y-7">
      <div>
        <h1 className="text-3xl font-extrabold text-slate-900">Оформление доставки</h1>
        <p className="mt-2 text-slate-500">Укажите адрес и данные получателя для подготовки доставки</p>
      </div>

      <div className="flex items-center justify-center gap-2 text-xs sm:gap-3 sm:text-sm">
        {steps.map((label, index) => {
          const number = index + 1;
          const active = step === number;
          const complete = step > number || submitted;
          return (
            <div className="flex items-center gap-2 sm:gap-3" key={label}>
              {index > 0 && <div className={`h-px w-5 sm:w-16 ${complete || active ? "bg-emerald-300" : "bg-slate-200"}`} />}
              <button
                type="button"
                onClick={() => number < step && setStep(number)}
                disabled={number >= step || submitted}
                className={`flex items-center gap-2 ${active ? "font-semibold text-emerald-800" : complete ? "text-emerald-700" : "text-slate-400"}`}
              >
                <span className={`flex h-8 w-8 items-center justify-center rounded-full ${active ? "bg-emerald-700 text-white" : complete ? "bg-emerald-100 text-emerald-700" : "border border-slate-200 bg-white"}`}>
                  {complete ? <CheckCircle2 size={17} /> : number}
                </span>
                <span>{label}</span>
              </button>
            </div>
          );
        })}
      </div>

      {submitted ? (
        <section className="mx-auto max-w-2xl rounded-2xl border border-emerald-200 bg-white p-8 text-center shadow-sm">
          <CheckCircle2 className="mx-auto text-emerald-600" size={48} />
          <h2 className="mt-4 text-2xl font-bold text-slate-900">Заказ оформлен</h2>
          <p className="mt-2 text-slate-600">Это демонстрационное подтверждение. Данные заказа пока не отправляются на сервер.</p>
          <div className="mt-6 rounded-xl bg-slate-50 p-4 text-left text-sm text-slate-600">
            <p><b>Адрес:</b> {rawAddress}</p>
            <p className="mt-2"><b>Получатель:</b> {recipient.name}, {recipient.phone}</p>
            <p className="mt-2"><b>Оплата:</b> {payment === "cash" ? "Наличными при получении" : "Картой при получении"}</p>
          </div>
          <button onClick={() => { setSubmitted(false); setStep(1); setRawAddress(""); setChecked(false); setRecipient({ name: "", phone: "", email: "", comment: "" }); setPayment(""); setError(""); }} className="mt-6 font-semibold text-emerald-700 hover:text-emerald-800">Оформить ещё один заказ</button>
        </section>
      ) : (
        <div className="grid items-start gap-6 xl:grid-cols-[1.3fr_1fr]">
          <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
            {step === 1 && <>
              <h2 className="text-2xl font-bold text-slate-900">Куда доставить заказ?</h2>
              <p className="mt-2 text-sm text-slate-500">Введите адрес так, как вам удобно</p>
              <div className="relative mt-6">
                <MapPin size={19} className="absolute left-4 top-1/2 -translate-y-1/2 text-emerald-600" />
                <input value={rawAddress} onChange={(event) => { setRawAddress(event.target.value); setChecked(false); setError(""); }} placeholder="Например: Алматы, мкр Аксай 3а, дом 59, кв 70" className={`${inputClass} py-4 pl-11`} />
              </div>
              <button onClick={checkAddress} className="mt-4 flex w-full items-center justify-center gap-2 rounded-xl bg-emerald-700 px-5 py-3 font-semibold text-white hover:bg-emerald-800"><Navigation size={18} />Проверить адрес</button>
              {checked && <div className="mt-4 flex items-center gap-2 text-sm font-medium text-emerald-700"><CheckCircle2 size={18} />Адрес указан. Автоматическая проверка пока не подключена.</div>}
              <div className="mt-8 rounded-xl border border-slate-100 bg-slate-50 p-4 text-sm text-slate-600">Адрес будет использован в демонстрационном оформлении. Проверка доступности доставки появится после подключения сервера.</div>
            </>}

            {step === 2 && <>
              <h2 className="text-2xl font-bold text-slate-900">Данные получателя</h2>
              <p className="mt-2 text-sm text-slate-500">Укажите, кому курьер передаст заказ.</p>
              <div className="mt-6 grid gap-4">
                {recipientValues.map((key, index) => <label key={key}>
                  <span className="mb-2 block text-sm font-medium text-slate-600">{fieldLabels[index]}</span>
                  <input type={key === "email" ? "email" : "text"} value={recipient[key]} onChange={(event) => setRecipient((current) => ({ ...current, [key]: event.target.value }))} placeholder={key === "phone" ? "+7 (___) ___-__-__" : key === "name" ? "Имя получателя" : "Можно не заполнять"} className={inputClass} />
                </label>)}
              </div>
            </>}

            {step === 3 && <>
              <h2 className="text-2xl font-bold text-slate-900">Способ оплаты</h2>
              <p className="mt-2 text-sm text-slate-500">Выберите, как оплатить заказ курьеру.</p>
              <div className="mt-6 grid gap-3">
                {([ ["cash", "Наличными при получении"], ["card", "Картой при получении"] ] as const).map(([value, label]) => <label key={value} className={`flex cursor-pointer items-center gap-3 rounded-xl border p-4 ${payment === value ? "border-emerald-500 bg-emerald-50" : "border-slate-200"}`}>
                  <input type="radio" name="payment" value={value} checked={payment === value} onChange={() => setPayment(value)} className="accent-emerald-700" />
                  <span className="font-medium text-slate-800">{label}</span>
                </label>)}
              </div>
              <p className="mt-4 text-xs text-slate-400">Оплата онлайн и списание средств не выполняются.</p>
            </>}

            {error && <div className="mt-5 flex gap-2 rounded-xl bg-amber-50 p-3 text-sm text-amber-800"><AlertCircle size={18} className="shrink-0" />{error}</div>}
            <div className="mt-8 flex gap-3 border-t border-slate-100 pt-6">
              {step > 1 && <button onClick={() => { setStep(step - 1); setError(""); }} className="flex items-center gap-2 rounded-xl border border-slate-200 px-5 py-3 font-semibold text-slate-700 hover:bg-slate-50"><ArrowLeft size={18} />Назад</button>}
              <button onClick={continueStep} className="flex flex-1 items-center justify-center gap-2 rounded-xl bg-emerald-700 px-5 py-3 font-semibold text-white hover:bg-emerald-800">{step === 3 ? "Подтвердить заказ" : "Продолжить"}<ArrowRight size={18} /></button>
            </div>
          </section>

          <aside className="space-y-4 rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
            <div className="flex items-start gap-3 rounded-xl bg-slate-50 p-4"><Package size={22} className="mt-0.5 shrink-0 text-emerald-700" /><div><p className="text-sm font-semibold text-slate-900">Адрес доставки</p><p className="mt-1 break-words text-sm text-slate-500">{rawAddress || "Адрес пока не указан"}</p></div></div>
            {step > 1 && <div className="rounded-xl bg-slate-50 p-4 text-sm"><p className="font-semibold text-slate-900">Получатель</p><p className="mt-1 text-slate-500">{recipient.name || "Имя пока не указано"}{recipient.phone && ` · ${recipient.phone}`}</p></div>}
            {step > 2 && <div className="rounded-xl bg-slate-50 p-4 text-sm"><p className="font-semibold text-slate-900">Оплата</p><p className="mt-1 text-slate-500">{payment === "cash" ? "Наличными при получении" : payment === "card" ? "Картой при получении" : "Не выбрана"}</p></div>}
            <div className="flex items-center gap-2 text-xs text-slate-400"><MapPin size={15} />Демо оформление: без отправки заказа на сервер</div>
          </aside>
        </div>
      )}
    </div>
  );
}
