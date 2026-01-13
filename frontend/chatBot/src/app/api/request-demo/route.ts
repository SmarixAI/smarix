import { NextResponse } from 'next/server';
import nodemailer from 'nodemailer';

console.log("Debugging Environment Variables:");
  console.log("SMTP_HOST:", process.env.SMTP_HOST);
  console.log("SMTP_USER:", process.env.SMTP_USER);
  console.log("SMTP_PASS length:", process.env.SMTP_PASSWORD ? process.env.SMTP_PASSWORD.length : "Undefined");

const transporter = nodemailer.createTransport({
  host: process.env.SMTP_HOST,
  port: Number(process.env.SMTP_PORT),
  secure: true, 
  auth: {
    user: process.env.SMTP_USER,
    pass: process.env.SMTP_PASSWORD,
  },
});

export async function POST(req: Request) {
  try {
    const body = await req.json();
    const { 
      firstName, lastName, email, fullPhone, 
      company, jobTitle, contactReason, message 
    } = body;

    if (!firstName || !email || !message) {
      return NextResponse.json({ error: 'Missing fields' }, { status: 400 });
    }

    const mailOptions = {
      from: process.env.SMTP_FROM || '"Smarix Web" <no-reply@smarix.net>',
      to: 'contact@smarix.net',
      subject: `New Inquiry: ${contactReason} from ${firstName} ${lastName}`,
      html: `
        <h2>New Contact Request</h2>
        <p><strong>Name:</strong> ${firstName} ${lastName}</p>
        <p><strong>Email:</strong> ${email}</p>
        <p><strong>Phone:</strong> ${fullPhone}</p>
        <p><strong>Company:</strong> ${company} (${jobTitle})</p>
        <p><strong>Reason:</strong> ${contactReason}</p>
        <br/>
        <h3>Message:</h3>
        <p>${message}</p>
      `,
    };

    await transporter.sendMail(mailOptions);

    return NextResponse.json({ success: true });
  } catch (error) {
    console.error('Email error:', error);
    return NextResponse.json({ error: 'Failed to send email' }, { status: 500 });
  }
}